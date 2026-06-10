package com.guidepedia.model.entity;

import jakarta.persistence.CascadeType;
import jakarta.persistence.Column;
import jakarta.persistence.Entity;
import jakarta.persistence.FetchType;
import jakarta.persistence.GeneratedValue;
import jakarta.persistence.GenerationType;
import jakarta.persistence.Id;
import jakarta.persistence.JoinColumn;
import jakarta.persistence.ManyToOne;
import jakarta.persistence.Table;
import lombok.Getter;
import lombok.Setter;
import lombok.experimental.Accessors;

import java.time.LocalDateTime;


@Getter
@Setter
@Accessors(chain = true)
@Entity
@Table(name = "comment", schema = "public")
public class CommentEntity {
    @Id
    @GeneratedValue(strategy = GenerationType.IDENTITY)
    private Long id;

    @ManyToOne(optional=false, cascade= CascadeType.MERGE, fetch= FetchType.EAGER)
    @JoinColumn(name="articleid")
    private ArticleEntity article;

    @ManyToOne(optional=false, cascade=CascadeType.MERGE, fetch= FetchType.EAGER)
    @JoinColumn(name="userid")
    private UserEntity user;

    @Column(name = "comment")
    private String comment;

    @Column(name = "createdat")
    private LocalDateTime createdAt;

    @Column(name = "parentcommentid")
    private Long parentCommentId;
}
