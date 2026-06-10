package com.guidepedia.model.response.stats;

import lombok.AllArgsConstructor;
import lombok.Getter;

@Getter
@AllArgsConstructor
public class CategoryStatEntry {
    private String categoryName;
    private long articleCount;
}
