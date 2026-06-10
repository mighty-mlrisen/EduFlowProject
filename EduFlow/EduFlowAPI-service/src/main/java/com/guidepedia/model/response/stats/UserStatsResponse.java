package com.guidepedia.model.response.stats;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.time.LocalDateTime;
import java.util.List;

@Getter
@AllArgsConstructor
public class UserStatsResponse {
    private long publishedArticles;
    private long drafts;
    private long commentsGiven;
    private long savedArticlesCount;
    private long totalLikesReceived;
    private double avgLikesPerArticle;
    private long followersCount;
    private long subscriptionsCount;
    private long articlesLast30Days;
    private long commentsLast30Days;
    private LocalDateTime lastPublicationDate;
    private List<ArticleStatEntry> top5ArticlesByLikes;
    private List<ArticleStatEntry> top5ArticlesByComments;
}
