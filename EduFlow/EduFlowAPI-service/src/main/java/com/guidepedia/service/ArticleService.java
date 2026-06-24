package com.guidepedia.service;

import com.guidepedia.exception.BusinessException;
import com.guidepedia.exception.ErrorMessage;
import com.guidepedia.exception.MyEntityNotFoundException;
import com.guidepedia.model.entity.ArticleEntity;
import com.guidepedia.model.entity.CategoryEntity;
import com.guidepedia.model.entity.CommentEntity;
import com.guidepedia.model.entity.UserEntity;
import com.guidepedia.model.request.ArticleRequest;
import com.guidepedia.model.request.CommentRequest;
import com.guidepedia.model.response.ArticleResponse;
import com.guidepedia.model.response.CommentResponse;
import com.guidepedia.model.response.ProfileResponse;
import com.guidepedia.repo.ArticleRepository;
import com.guidepedia.repo.CategoryRepository;
import com.guidepedia.repo.CommentRepository;
import com.guidepedia.repo.UserRepository;
import com.guidepedia.security.services.UserDetailsImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.cache.annotation.CachePut;
import org.springframework.cache.annotation.Cacheable;
import org.springframework.security.core.userdetails.UserDetails;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.stream.Collectors;

@Service
public class ArticleService {
    @Autowired
    UserRepository userRepository;

    @Autowired
    CommentRepository commentRepository;

    @Autowired
    CategoryRepository categoryRepository;

    @Autowired
    ArticleRepository articleRepository;

    @Autowired
    UserService userService;

    @Autowired
    SummarizationClient summarizationClient;

    private ArticleResponse buildResponse(ArticleEntity article, UserEntity user) {
        ArticleResponse r = new ArticleResponse(article, user);
        r.setCommentsCount((int) commentRepository.countByArticle(article));
        return r;
    }

    private List<ArticleResponse> buildResponseList(List<ArticleEntity> articles, UserEntity user) {
        return articles.stream()
                .map(a -> buildResponse(a, user))
                .collect(Collectors.toList());
    }

    @Transactional
    @CachePut(value = "articles")
    public ArticleResponse createArticle(ArticleRequest articleRequest, UserDetailsImpl user) {
        ArticleEntity articleEntity = new ArticleEntity();
        UserEntity userEntity = userService.getUser(user);
        articleEntity.setCreatedBy(userEntity);
        articleEntity.setCategory(categoryRepository.findByName(articleRequest.getCategoryName())
                .orElseThrow(() -> new MyEntityNotFoundException(articleRequest.getCategoryName())));
        articleEntity.setTitle(articleRequest.getTitle());
        articleEntity.setText(articleRequest.getText());
        articleEntity.setDescription(articleRequest.getDescription());
        articleEntity.setCreatedAt(LocalDateTime.now());
        articleEntity.setDraft(articleRequest.getDraft());
        articleEntity.setImage(articleRequest.getImage());
        articleEntity.setUsers(new HashSet<>());
        return buildResponse(articleRepository.save(articleEntity), userEntity);
    }

    @Transactional(readOnly = true)
    public ArticleResponse getArticleById(Long articleId, UserDetailsImpl user) {
        ArticleEntity article = articleRepository.findById(articleId)
                .orElseThrow(() -> new MyEntityNotFoundException(articleId));
        return buildResponse(article, userService.getUser(user));
    }

    @Transactional(readOnly = true)
    public List<ArticleResponse> getUserArticle(UserDetailsImpl user) {
        UserEntity userEntity = userService.getUser(user);
        return buildResponseList(articleRepository.findAllByCreatedByOrderByCreatedAtDesc(userEntity), userEntity);
    }

    @Transactional(readOnly = true)
    public List<ArticleResponse> getArticleByCategoryId(Integer categoryId, UserDetailsImpl user) {
        UserEntity userEntity = userService.getUser(user);
        if (!categoryRepository.existsById(categoryId)) {
            throw new MyEntityNotFoundException(categoryId.longValue());
        }
        return buildResponseList(articleRepository.findAllByCategoryIdOrderByCreatedAtDesc(categoryId), userEntity);
    }

    @Transactional(readOnly = true)
    public List<ArticleResponse> getArticleByUserId(UserEntity user, UserEntity currentUser) {
        return buildResponseList(articleRepository.findAllByCreatedByOrderByCreatedAtDesc(user), currentUser);
    }

    @Transactional(readOnly = true)
    public List<ArticleResponse> getArticlesByUserId(Long userId, UserDetailsImpl currentUser) {
        UserEntity author = userRepository.findById(userId)
                .orElseThrow(() -> new MyEntityNotFoundException(userId));
        UserEntity currentUserEntity = userService.getUser(currentUser);
        return getArticleByUserId(author, currentUserEntity);
    }

    @Transactional(readOnly = true)
    public List<ArticleResponse> getAllArticle(UserDetailsImpl user) {
        UserEntity userEntity = userService.getUser(user);
        return buildResponseList(articleRepository.findAll(), userEntity);
    }

    @Transactional(readOnly = true)
    public List<CategoryEntity> getAllCategories() {
        return categoryRepository.findAll();
    }

    @Transactional(readOnly = true)
    public List<ArticleResponse> getUserArticleDrafts(UserDetailsImpl user) {
        UserEntity userEntity = userRepository.findById(user.getId())
                .orElseThrow(() -> new MyEntityNotFoundException(user.getId()));
        return buildResponseList(
                articleRepository.findAllByCreatedByAndDraftOrderByCreatedAtDesc(userEntity, true), userEntity);
    }

    @Transactional
    public ArticleResponse createReaction(Long articleId, Boolean reaction, UserDetailsImpl user) {
        ArticleEntity article = articleRepository.findById(articleId).orElseThrow(() -> new MyEntityNotFoundException(articleId));
        UserEntity userEntity = userService.getUser(user);

        boolean contains = article.getUsers().contains(userEntity);
        if (contains && !reaction) {
            article.getUsers().remove(userEntity);
            userEntity.getArticlesReaction().remove(article);
        } else if (!contains && reaction) {
            article.getUsers().add(userEntity);
            userEntity.getArticlesReaction().add(article);
        } else {
            throw new BusinessException("Object already exist or deleted");
        }
        articleRepository.save(article);
        return buildResponse(article, userEntity);
    }

    @Transactional(readOnly = true)
    public List<ArticleResponse> getSubscribtionArticles(UserDetailsImpl user) {
        UserEntity userEntity = userService.getUser(user);
        return userEntity.getSubscriptions().stream()
                .flatMap(s -> getArticleByUserId(s, userEntity).stream())
                .distinct().collect(Collectors.toList());
    }

    @Transactional
    public CommentResponse createComment(Long articleId, UserDetailsImpl user, CommentRequest commentRequest) {
        CommentEntity comment = new CommentEntity();
        UserEntity userEntity = userService.getUser(user);
        comment.setArticle(articleRepository.findById(articleId)
                .orElseThrow(() -> new MyEntityNotFoundException(articleId)));
        comment.setUser(userEntity);
        comment.setComment(commentRequest.getComment());
        comment.setCreatedAt(LocalDateTime.now());
        comment.setParentCommentId(commentRequest.getParentCommentId());
        commentRepository.save(comment);
        return new CommentResponse(comment, userEntity);
    }

    @Transactional(readOnly = true)
    public List<CommentResponse> getAllComments(Long articleId, UserDetailsImpl user) {
        CommentResponse commentResponse = new CommentResponse();
        UserEntity userEntity = userService.getUser(user);
        return commentResponse.getListCommentResponces(commentRepository.findByArticle(articleRepository.findById(articleId)
                .orElseThrow(() -> new MyEntityNotFoundException(articleId))), userEntity);
    }

    @Transactional(readOnly = true)
    public List<ArticleResponse> getSearchArticle(String line, UserDetailsImpl user) {
        UserEntity userEntity = userService.getUser(user);
        return buildResponseList(articleRepository.findByTitleContainingIgnoreCase(line), userEntity);
    }

    @Transactional(readOnly = true)
    public Integer getCountReactions(Long articleId, UserDetailsImpl user) {
        UserEntity userEntity = userService.getUser(user);
        ArticleResponse articleResponse = new ArticleResponse(articleRepository.findById(articleId).orElseThrow(() -> new MyEntityNotFoundException(articleId)), userEntity);
        return articleResponse.getLikes();
    }

    @Transactional(readOnly = true)
    public String getArticleSummary(Long articleId, UserDetailsImpl user) {
        articleRepository.findById(articleId)
                .orElseThrow(() -> new MyEntityNotFoundException(articleId));
        return summarizationClient.getSummary(articleId);
    }

    @Transactional(readOnly = true)
    public String getArticleText(Long articleId) {
        ArticleEntity article = articleRepository.findById(articleId)
                .orElseThrow(() -> new MyEntityNotFoundException(articleId));
        return article.getText() != null ? article.getText() : "";
    }

    @Transactional
    public void deleteArticle(Long articleId, UserDetailsImpl user) {
        ArticleEntity article = articleRepository.findById(articleId)
                .orElseThrow(() -> new MyEntityNotFoundException(articleId));
        UserEntity userEntity = userService.getUser(user);
        if (!article.getCreatedBy().getId().equals(userEntity.getId())) {
            throw new BusinessException("Access denied: not the author");
        }
        articleRepository.deleteById(articleId);
        summarizationClient.invalidateCache(articleId);
    }

    @Transactional
    public ArticleResponse updateArticle(ArticleRequest articleRequest, UserDetailsImpl user, Long articleId) {
        ArticleEntity article = articleRepository.findById(articleId)
                .orElseThrow(() -> new MyEntityNotFoundException(articleId));
        article.setCategory(categoryRepository.findByName(articleRequest.getCategoryName())
                .orElseThrow(() -> new MyEntityNotFoundException(articleRequest.getCategoryName())));
        article.setDraft(articleRequest.getDraft());
        article.setDescription(articleRequest.getDescription());
        article.setTitle(articleRequest.getTitle());
        article.setText(articleRequest.getText());
        article.setImage(articleRequest.getImage());
        articleRepository.save(article);
        summarizationClient.invalidateCache(articleId);
        return buildResponse(article, userService.getUser(user));
    }
}