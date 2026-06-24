package com.guidepedia.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.HttpEntity;
import org.springframework.http.HttpHeaders;
import org.springframework.http.HttpMethod;
import org.springframework.http.MediaType;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.Map;

@Service
public class SummarizationClient {

    private static final Logger log = LoggerFactory.getLogger(SummarizationClient.class);

    private final RestTemplate restTemplate;
    private final RestTemplate fastRestTemplate;
    private final String summarizeUrl;
    private final String cacheUrl;

    public SummarizationClient(
            @Value("${summarization.service.url:http://localhost:8000}") String serviceUrl) {

        // 5 min timeout for model inference
        SimpleClientHttpRequestFactory slowFactory = new SimpleClientHttpRequestFactory();
        slowFactory.setConnectTimeout(5_000);
        slowFactory.setReadTimeout(300_000);
        this.restTemplate = new RestTemplate(slowFactory);

        // 3 sec timeout for cache invalidation (fire-and-forget)
        SimpleClientHttpRequestFactory fastFactory = new SimpleClientHttpRequestFactory();
        fastFactory.setConnectTimeout(2_000);
        fastFactory.setReadTimeout(3_000);
        this.fastRestTemplate = new RestTemplate(fastFactory);

        this.summarizeUrl = serviceUrl + "/api/summarize/";
        this.cacheUrl = serviceUrl + "/api/cache/{articleId}/";
    }

    public String getSummary(Long articleId) {
        HttpHeaders headers = new HttpHeaders();
        headers.setContentType(MediaType.APPLICATION_JSON);

        HttpEntity<Map<String, Object>> request = new HttpEntity<>(
                Map.of("article_id", articleId), headers);

        Map<?, ?> response = restTemplate.postForObject(summarizeUrl, request, Map.class);
        if (response == null || !response.containsKey("summary")) {
            throw new RuntimeException("Summarization service returned unexpected response");
        }
        return (String) response.get("summary");
    }

    public void invalidateCache(Long articleId) {
        try {
            fastRestTemplate.exchange(cacheUrl, HttpMethod.DELETE, null, Void.class, articleId);
        } catch (Exception e) {
            log.warn("Failed to invalidate summary cache for article {}: {}", articleId, e.getMessage());
        }
    }
}
