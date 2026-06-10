package com.guidepedia.model.response.stats;

import lombok.AllArgsConstructor;
import lombok.Getter;

import java.util.List;

@Getter
@AllArgsConstructor
public class GlobalStatsResponse {
    private long totalUsers;
    private long totalArticles;
    private long totalPublished;
    private long totalDrafts;
    private long totalComments;
    private long totalLikes;
    private long totalSubscriptions;
    private long newUsersLastWeek;
    private List<ArticleStatEntry> top10ArticlesByLikes;
    private List<AuthorStatEntry> top10AuthorsByLikes;
    private List<AuthorStatEntry> top10AuthorsBySubscribers;
    private List<CategoryStatEntry> categoryStats;
}
