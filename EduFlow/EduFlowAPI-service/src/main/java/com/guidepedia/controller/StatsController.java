package com.guidepedia.controller;

import com.guidepedia.model.response.stats.GlobalStatsResponse;
import com.guidepedia.model.response.stats.UserStatsResponse;
import com.guidepedia.security.services.UserDetailsImpl;
import com.guidepedia.service.StatsService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.security.SecurityRequirement;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.CrossOrigin;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.RestController;

@RestController
@SecurityRequirement(name = "Authorization")
@Tag(description = "Api for platform and user statistics", name = "Statistics Resource")
@CrossOrigin
public class StatsController {

    @Autowired
    private StatsService statsService;

    @Operation(summary = "Global platform statistics",
               description = "Totals, top-10 articles/authors, category breakdown, new users last week")
    @GetMapping("/stats/global")
    public GlobalStatsResponse getGlobalStats(@AuthenticationPrincipal UserDetailsImpl user) {
        return statsService.getGlobalStats();
    }

    @Operation(summary = "Current user statistics",
               description = "Personal counts, top articles, activity over last 30 days")
    @GetMapping("/user/stats")
    public UserStatsResponse getUserStats(@AuthenticationPrincipal UserDetailsImpl user) {
        return statsService.getUserStats(user);
    }
}
