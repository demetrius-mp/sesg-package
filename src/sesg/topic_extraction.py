"""
Topic extraction module.

This module is responsible to provide strategies to extract topics of a set
of documents.

Currently, the only available strategies are
[LDA (Latent Dirichlet Allocation)](https://www.jmlr.org/papers/volume3/blei03a/blei03a.pdf?ref=https://githubhelp.com),
and [BERTopic](https://arxiv.org/abs/2203.05794).
"""  # noqa: E501

from enum import Enum
from typing import Any, List

from sklearn.feature_extraction.text import CountVectorizer


class TopicExtractionStrategy(str, Enum):
    """
    Enum defining the available topic extraction strategies.

    Examples:
        >>> lda_strategy = TopicExtractionStrategy.lda
        >>> lda_strategy.value
        'lda'
    """

    lda = "lda"
    bertopic = "bertopic"


def extract_topics_with_lda(
    *,
    docs: List[str],
    min_document_frequency: float,
    number_of_topics: int,
) -> List[List[str]]:
    """
    Extracts topics from a list of documents using LDA method.

    Args:
        docs (List[str]): List of documents.
        min_document_frequency (float): CountVectorizer parameter - Minimum document frequency for the word to appear on the bag of words.
        number_of_topics (int): LDA parameter - Number of topics to generate.

    Returns:
        List of topics, where a topic is a list of words.

    Examples:
        >>> extract_topics_with_lda(  # doctest: +SKIP
        ...     docs=["detecting code smells with machine learning", "code smells detection tools", "error detection in Java software with machine learning"],
        ...     min_document_frequency=0.1,
        ...     number_of_topics=2,
        ... )
        [["word1 topic1", "word2 topic1"], ["word1 topic2", "word2 topic2"]]
    """  # noqa: E501
    from sklearn.decomposition import LatentDirichletAllocation

    # without this "Any typings", pylance takes too long to analyze the sklearn files
    # remove this line once sklearn has developed stubs for the package
    LatentDirichletAllocation: Any

    vectorizer = CountVectorizer(
        min_df=min_document_frequency,
        max_df=1.0,
        ngram_range=(1, 3),
        max_features=None,
        stop_words="english",
    )

    tf = vectorizer.fit_transform(docs)

    # `feature_names` is a list with the vectorized words from the document.
    # meaning `feature_names[i]` is a token in the text.
    feature_names = vectorizer.get_feature_names_out()

    alpha = None
    beta = None
    learning = "batch"  # Batch or Online

    # Run the Latent Dirichlet Allocation (LDA) algorithm and train it.
    lda = LatentDirichletAllocation(
        n_components=number_of_topics,
        doc_topic_prior=alpha,
        topic_word_prior=beta,
        learning_method=learning,
        learning_decay=0.7,
        learning_offset=10.0,
        max_iter=5000,
        batch_size=128,
        evaluate_every=-1,
        total_samples=1000000.0,
        perp_tol=0.1,
        mean_change_tol=0.001,
        max_doc_update_iter=100,
        random_state=0,
    )

    lda.fit(tf)

    # `lda.components_` hold the entire list of topics found by LDA.
    # notice that for `lda.components_`, the topic is a list of indexes
    # where the index will map to a token (~word) in `feature_names`.
    # as an example, the next line gets all tokens of the first topic

    # first_topic = lda.components_[0]
    # topic_words = [feature_names[i] for i in first_topic]

    # `topic.argsort()` will return the indexes that would sort the topics,
    # in ascending order
    # since we want the most latent topics, we reverse the list with `[::-1]`

    topics: List[List[str]] = [
        [feature_names[i] for i in topic.argsort()[::-1]] for topic in lda.components_
    ]

    return topics


def extract_topics_with_bertopic(
    *,
    docs: List[str],
    top_n_words: int,
    min_topic_size: int,
    umap_n_neighbors: int,
) -> List[List[str]]:
    """
    Extracts topics from a list of documents using BERTopic.

    Args:
        docs (List[str]): List of documents.
        top_n_words (int): Number of words per topic to extract. Setting this too high can negatively impact topic embeddings as topics are typically best represented by at most 10 words.
        min_topic_size (int): Minimum size of the topic. Increasing this value will lead to a lower number of clusters/topics.
        umap_n_neighbors (int): Number of neighboring sample points used when making the manifold approximation. Increasing this value typically results in a more global view of the embedding structure whilst smaller values result in a more local view. Increasing this value often results in larger clusters being created.

    Returns:
        List of topics, where a topic is a list of words.

    Examples:
        >>> extract_topics_with_bertopic(  # doctest: +SKIP
        ...     docs=["detecting code smells with machine learning", "code smells detection tools", "error detection in Java software with machine learning"],
        ... )
        [["word1 topic1", "word2 topic1"], ["word1 topic2", "word2 topic2"]]
    """  # noqa: E501
    from bertopic import BERTopic
    from umap.umap_ import UMAP

    vectorizer_model = CountVectorizer(
        stop_words="english",
        ngram_range=(1, 3),
    )

    umap_model = UMAP(
        n_neighbors=umap_n_neighbors,
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        low_memory=False,
    )

    topic_model = BERTopic(
        language="english",
        verbose=True,
        top_n_words=top_n_words,
        min_topic_size=min_topic_size,
        vectorizer_model=vectorizer_model,
        umap_model=umap_model,
    )

    topic_model.fit_transform(docs)

    # topic_model.get_topics() will return a Mapping where
    # the key is the index of the topic,
    # and the value is a list of tuples
    # the tuple is composed of a word (or token), and its score

    topics: List[List[str]] = [
        [word for word, _ in topic_group]  # type: ignore
        for topic_group in topic_model.get_topics().values()
    ]

    return topics
