package com.guidepedia.model.response.stats;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class ArticleStatEntry {
    private Long articleId;
    private String title;
    private String authorUsername;
    private String authorAvatar;
    private long count;
}
