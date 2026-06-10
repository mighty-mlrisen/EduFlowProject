package com.guidepedia.model.response.stats;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class AuthorStatEntry {
    private Long userId;
    private String username;
    private String login;
    private String avatar;
    private long count;
}
