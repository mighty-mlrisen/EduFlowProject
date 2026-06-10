
package com.guidepedia.service;


import com.guidepedia.exception.BusinessException;
import com.guidepedia.exception.MyEntityNotFoundException;
import com.guidepedia.model.entity.ArticleEntity;
import com.guidepedia.model.entity.UserEntity;
import com.guidepedia.model.request.AuthRequest;
import com.guidepedia.model.request.SignUpRequest;
import com.guidepedia.model.response.ArticleResponse;
import com.guidepedia.model.response.ProfileResponse;
import com.guidepedia.repo.ArticleRepository;
import com.guidepedia.repo.CommentRepository;
import com.guidepedia.repo.UserRepository;
import com.guidepedia.security.jwt.JwtUtils;
import com.guidepedia.security.services.UserDetailsImpl;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.util.List;
import java.util.Objects;


@Service
public class UserService {

    @Autowired
    UserRepository userRepository;

    @Autowired
    ArticleRepository articleRepository;

    @Autowired
    CommentRepository commentRepository;

    @Transactional(readOnly = true)
    public UserEntity getUser(UserDetailsImpl user) {
        return userRepository.findById(user.getId())
                .orElseThrow(() -> new MyEntityNotFoundException(user.getId()));
    }

    @Transactional(readOnly = true)
    public ProfileResponse getProfile(UserDetailsImpl user){
        UserEntity userEntity = getUser(user);
        return new ProfileResponse(userEntity, userEntity.getSubscribers().contains(userEntity));
    }

    @Transactional
    public ProfileResponse updateProfile(ProfileResponse profileResponse, UserDetailsImpl user){
        UserEntity userEntity = getUser(user);
        userEntity.setUsername(profileResponse.getUsername());
        userEntity.setAvatar(profileResponse.getAvatar());
        userEntity.setProfile(profileResponse.getProfile());
        userEntity.setCardDetails(profileResponse.getCardDetails());
        userRepository.save(userEntity);
        return new ProfileResponse(userEntity, userEntity.getSubscribers().contains(userEntity));
    }

    private ArticleResponse buildResponse(ArticleEntity article, UserEntity user) {
        ArticleResponse r = new ArticleResponse(article, user);
        r.setCommentsCount((int) commentRepository.countByArticle(article));
        return r;
    }

    @Transactional
    public ArticleResponse changeSaveArticle(Long articleId, Boolean status, UserDetailsImpl user) {
        ArticleEntity article = articleRepository.findById(articleId).orElseThrow(() -> new MyEntityNotFoundException(articleId));
        UserEntity userEntity = getUser(user);
        boolean contains = article.getSavedUsers().contains(userEntity);
        if (contains && !status) {
            article.getSavedUsers().remove(userEntity);
            userEntity.getSavedArticles().remove(article);
        } else if (!contains && status) {
            article.getSavedUsers().add(userEntity);
            userEntity.getSavedArticles().add(article);
        }
        else {
            throw new BusinessException("Object already exist or deleted");
        }
        articleRepository.save(article);
        return buildResponse(article, userEntity);
    }

    @Transactional(readOnly = true)
    public List<ArticleResponse> getSavedArticles(UserDetailsImpl user) {
        UserEntity userEntity = getUser(user);
        return userEntity.getSavedArticles().stream()
                .map(a -> buildResponse(a, userEntity))
                .collect(java.util.stream.Collectors.toList());
    }

    @Transactional
    public ProfileResponse changeStatusSubscribtion(Long userId, Boolean status, UserDetailsImpl user) {
        UserEntity currentUser = getUser(user);
        UserEntity publisher = userRepository.findById(userId)
                .orElseThrow(() -> new MyEntityNotFoundException(userId));
        if (publisher.equals(currentUser)) {
            throw new BusinessException("User try to subscribe to himself");
        }
        boolean contains = publisher.getSubscribers().contains(currentUser);
        if (contains && !status) {
            publisher.getSubscribers().remove(currentUser);
            currentUser.getSubscriptions().remove(publisher);
        }
        else if (!contains && status){
            publisher.getSubscribers().add(currentUser);
            currentUser.getSubscriptions().add(publisher);
        } else {
            throw new BusinessException("Object already exist or deleted");
        }
        userRepository.save(publisher);
        System.out.println(currentUser.getSubscriptions().stream().map(UserEntity::getLogin).toList());
        return new ProfileResponse(publisher, publisher.getSubscribers().contains(currentUser));
    }

    @Transactional(readOnly = true)
    public List<ProfileResponse> getSubscribers(UserDetailsImpl user) {
        ProfileResponse profileResponse = new ProfileResponse();
        UserEntity userEntity = getUser(user);
        return profileResponse.getListProfileResponces(userEntity.getSubscribers().stream().toList(), userEntity);
    }

    @Transactional(readOnly = true)
    public List<ProfileResponse> getSubscribtions(UserDetailsImpl user) {
        ProfileResponse profileResponse = new ProfileResponse();
        UserEntity userEntity = getUser(user);
        System.out.println(userEntity.getLogin());
        System.out.println(userEntity.getSubscriptions().stream().map(UserEntity::getLogin).toList());
        return profileResponse.getListProfileResponces(userEntity.getSubscriptions().stream().toList(), userEntity);
    }

    @Transactional(readOnly = true)
    public List<ProfileResponse> getUserSubscribtions(UserDetailsImpl user, Long userId) {
        ProfileResponse profileResponse = new ProfileResponse();
        UserEntity userEntity = userRepository.findById(userId)
                .orElseThrow(() -> new MyEntityNotFoundException(userId));
        UserEntity currentUser = getUser(user);
        return profileResponse.getListProfileResponces(userEntity.getSubscriptions().stream().toList(), currentUser);
    }

    @Transactional(readOnly = true)
    public List<ProfileResponse> getUserSubscribers(UserDetailsImpl user, Long userId) {
        ProfileResponse profileResponse = new ProfileResponse();
        UserEntity userEntity = userRepository.findById(userId)
                .orElseThrow(() -> new MyEntityNotFoundException(userId));
        UserEntity currentUser = getUser(user);
        return profileResponse.getListProfileResponces(userEntity.getSubscribers().stream().toList(), currentUser);
    }

    @Transactional(readOnly = true)
    public ProfileResponse getProfileById(UserDetailsImpl user, Long userId) {
        UserEntity userEntity = userRepository.findById(userId)
                .orElseThrow(() -> new MyEntityNotFoundException(userId));
        UserEntity currentUser = getUser(user);
        return new ProfileResponse(userEntity, userEntity.getSubscribers().contains(currentUser));
    }

    @Transactional(readOnly = true)
    public List<ProfileResponse> searchByUsername(String username, UserDetailsImpl user) {
        UserEntity currentUser = getUser(user);
        ProfileResponse profileResponse = new ProfileResponse();
        return profileResponse.getListProfileResponces(
                userRepository.findByUsernameContainingIgnoreCase(username), currentUser);
    }
}
