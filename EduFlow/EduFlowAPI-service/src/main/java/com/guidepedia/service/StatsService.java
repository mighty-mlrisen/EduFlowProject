package com.guidepedia.service;

import com.guidepedia.model.entity.UserEntity;
import com.guidepedia.model.response.stats.*;
import com.guidepedia.repo.ArticleRepository;
import com.guidepedia.repo.CommentRepository;
import com.guidepedia.repo.UserRepository;
import com.guidepedia.security.services.UserDetailsImpl;
import jakarta.persistence.EntityManager;
import jakarta.persistence.PersistenceContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.List;
import java.util.stream.Collectors;

@Service
@Transactional(readOnly = true)
public class StatsService {

    @Autowired
    private UserRepository userRepository;
    @Autowired
    private ArticleRepository articleRepository;
    @Autowired
    private CommentRepository commentRepository;
    @Autowired
    private UserService userService;
    @PersistenceContext
    private EntityManager em;

    // ── Global ─────────────────────────────────────────────────────────────────

    public GlobalStatsResponse getGlobalStats() {
        long totalUsers       = userRepository.count();
        long totalArticles    = articleRepository.count();
        long totalPublished   = articleRepository.countByDraftFalse();
        long totalDrafts      = articleRepository.countByDraftTrue();
        long totalComments    = commentRepository.count();
        long totalLikes       = toLong(em.createNativeQuery(
                "SELECT COUNT(*) FROM public.reaction").getSingleResult());
        long totalSubs        = toLong(em.createNativeQuery(
                "SELECT COUNT(*) FROM public.subscribtion").getSingleResult());
        long newUsersLastWeek = userRepository.countByCreatedAtAfter(
                LocalDateTime.now().minusDays(7));

        List<ArticleStatEntry> top10ByLikes = mapArticleRows(
                em.createNativeQuery(
                        "SELECT a.id, a.title, u.username, u.avatar, COUNT(r.userid) AS cnt " +
                        "FROM public.article a " +
                        "JOIN public.users u ON u.id = a.createdby " +
                        "LEFT JOIN public.reaction r ON r.articleid = a.id " +
                        "WHERE a.draft = false " +
                        "GROUP BY a.id, a.title, u.username, u.avatar " +
                        "ORDER BY cnt DESC " +
                        "LIMIT 10"
                ).getResultList());

        List<AuthorStatEntry> top10AuthorsByLikes = mapAuthorRows(
                em.createNativeQuery(
                        "SELECT u.id, u.username, u.login, u.avatar, COUNT(r.userid) AS cnt " +
                        "FROM public.users u " +
                        "LEFT JOIN public.article a ON a.createdby = u.id AND a.draft = false " +
                        "LEFT JOIN public.reaction r ON r.articleid = a.id " +
                        "GROUP BY u.id, u.username, u.login, u.avatar " +
                        "ORDER BY cnt DESC " +
                        "LIMIT 10"
                ).getResultList());

        List<AuthorStatEntry> top10AuthorsBySubscribers = mapAuthorRows(
                em.createNativeQuery(
                        "SELECT u.id, u.username, u.login, u.avatar, COUNT(s.subscriberid) AS cnt " +
                        "FROM public.users u " +
                        "LEFT JOIN public.subscribtion s ON s.publisherid = u.id " +
                        "GROUP BY u.id, u.username, u.login, u.avatar " +
                        "ORDER BY cnt DESC " +
                        "LIMIT 10"
                ).getResultList());

        List<CategoryStatEntry> categoryStats = ((List<Object[]>) em.createNativeQuery(
                "SELECT c.categoryname, COUNT(a.id) AS cnt " +
                "FROM public.category c " +
                "LEFT JOIN public.article a ON a.categoryid = c.id AND a.draft = false " +
                "GROUP BY c.id, c.categoryname " +
                "ORDER BY cnt DESC"
        ).getResultList()).stream()
                .map(row -> new CategoryStatEntry((String) row[0], toLong(row[1])))
                .collect(Collectors.toList());

        return new GlobalStatsResponse(
                totalUsers, totalArticles, totalPublished, totalDrafts,
                totalComments, totalLikes, totalSubs, newUsersLastWeek,
                top10ByLikes, top10AuthorsByLikes, top10AuthorsBySubscribers, categoryStats
        );
    }

    // ── User ───────────────────────────────────────────────────────────────────

    public UserStatsResponse getUserStats(UserDetailsImpl userDetails) {
        UserEntity user = userService.getUser(userDetails);
        Long userId = user.getId();

        long publishedArticles = articleRepository.countByCreatedByAndDraftFalse(user);
        long drafts            = articleRepository.countByCreatedByAndDraftTrue(user);
        long commentsGiven     = commentRepository.countByUser(user);

        long savedArticlesCount = toLong(em.createNativeQuery(
                "SELECT COUNT(*) FROM public.saved_article WHERE userid = :uid")
                .setParameter("uid", userId).getSingleResult());

        long totalLikesReceived = toLong(em.createNativeQuery(
                "SELECT COUNT(*) FROM public.reaction r " +
                "JOIN public.article a ON r.articleid = a.id " +
                "WHERE a.createdby = :uid AND a.draft = false")
                .setParameter("uid", userId).getSingleResult());

        double avgLikesPerArticle = publishedArticles > 0
                ? (double) totalLikesReceived / publishedArticles : 0.0;

        long followersCount = toLong(em.createNativeQuery(
                "SELECT COUNT(*) FROM public.subscribtion WHERE publisherid = :uid")
                .setParameter("uid", userId).getSingleResult());

        long subscriptionsCount = toLong(em.createNativeQuery(
                "SELECT COUNT(*) FROM public.subscribtion WHERE subscriberid = :uid")
                .setParameter("uid", userId).getSingleResult());

        LocalDateTime thirtyDaysAgo = LocalDateTime.now().minusDays(30);
        long articlesLast30Days = articleRepository
                .countByCreatedByAndDraftFalseAndCreatedAtAfter(user, thirtyDaysAgo);
        long commentsLast30Days = commentRepository
                .countByUserAndCreatedAtAfter(user, thirtyDaysAgo);

        Object lastPubRaw = em.createNativeQuery(
                "SELECT MAX(a.createdat) FROM public.article a " +
                "WHERE a.createdby = :uid AND a.draft = false")
                .setParameter("uid", userId).getSingleResult();
        LocalDateTime lastPublicationDate = toLocalDateTime(lastPubRaw);

        List<ArticleStatEntry> top5ByLikes = mapUserArticleRows(
                em.createNativeQuery(
                        "SELECT a.id, a.title, COUNT(r.userid) AS cnt " +
                        "FROM public.article a " +
                        "LEFT JOIN public.reaction r ON r.articleid = a.id " +
                        "WHERE a.createdby = :uid AND a.draft = false " +
                        "GROUP BY a.id, a.title " +
                        "ORDER BY cnt DESC " +
                        "LIMIT 5")
                        .setParameter("uid", userId).getResultList());

        List<ArticleStatEntry> top5ByComments = mapUserArticleRows(
                em.createNativeQuery(
                        "SELECT a.id, a.title, COUNT(c.id) AS cnt " +
                        "FROM public.article a " +
                        "LEFT JOIN public.comment c ON c.articleid = a.id " +
                        "WHERE a.createdby = :uid AND a.draft = false " +
                        "GROUP BY a.id, a.title " +
                        "ORDER BY cnt DESC " +
                        "LIMIT 5")
                        .setParameter("uid", userId).getResultList());

        return new UserStatsResponse(
                publishedArticles, drafts, commentsGiven, savedArticlesCount,
                totalLikesReceived, avgLikesPerArticle,
                followersCount, subscriptionsCount,
                articlesLast30Days, commentsLast30Days,
                lastPublicationDate, top5ByLikes, top5ByComments
        );
    }

    // ── Helpers ────────────────────────────────────────────────────────────────

    private static long toLong(Object val) {
        return val == null ? 0L : ((Number) val).longValue();
    }

    private static LocalDateTime toLocalDateTime(Object val) {
        if (val == null) return null;
        if (val instanceof LocalDateTime) return (LocalDateTime) val;
        if (val instanceof java.sql.Timestamp) return ((java.sql.Timestamp) val).toLocalDateTime();
        return null;
    }

    @SuppressWarnings("unchecked")
    private static List<ArticleStatEntry> mapArticleRows(List<Object[]> rows) {
        return rows.stream().map(r -> new ArticleStatEntry(
                toLong(r[0]), (String) r[1], (String) r[2], (String) r[3], toLong(r[4])
        )).collect(Collectors.toList());
    }

    @SuppressWarnings("unchecked")
    private static List<ArticleStatEntry> mapUserArticleRows(List<Object[]> rows) {
        return rows.stream().map(r -> new ArticleStatEntry(
                toLong(r[0]), (String) r[1], null, null, toLong(r[2])
        )).collect(Collectors.toList());
    }

    @SuppressWarnings("unchecked")
    private static List<AuthorStatEntry> mapAuthorRows(List<Object[]> rows) {
        return rows.stream().map(r -> new AuthorStatEntry(
                toLong(r[0]), (String) r[1], (String) r[2], (String) r[3], toLong(r[4])
        )).collect(Collectors.toList());
    }
}
