# Overview  

Our solution was an end-to-end pipeline that transformed unstructured data into a structured, visualizable, and searchable **knowledge graph**. By employing **Retrieval-Augmented Generation (RAG)** techniques—including **vector similarity, knowledge graph, and hybrid (vector + knowledge graph) searches**—our project aimed to enhance **searchability, discoverability, and AI-driven analytics** of qualitative insights.  

## How To Run

Coming Soon 

## How We Built It  

At the core of our application, we leveraged **Neo4j** both as a **vector store** and a **knowledge graph**, alongside **OpenAI’s embedding models** for generating vector representations and identifying key entities within text.  

## RAG Methods Used  

- **Vector Similarity Search** – Utilized Neo4j as a vector store, implementing a **chunking strategy** to ensure each entity had a manageable size. To provide relevant context to the LLM, user queries were embedded and compared against stored vectors to retrieve the most relevant information.  

- **Knowledge Graph-Only Search** – Neo4j housed **data relationships** created by the LLM. Contextual information was retrieved by dynamically generating **Cypher queries** based on the user prompt, allowing for structured and relationship-driven responses.  

- **Hybrid Search (Vector + Knowledge Graph)** – Neo4j stored both **structured and unstructured data**, representing chunked entities and linking related entities within the text. Our search process first leveraged **vector similarity** to find the most relevant chunks, followed by a **graph-based query** to retrieve additional context by identifying related entities and their connected data.  

## Final Thoughts  

It was exciting to explore these technologies and techniques over the past week. Through both implementation and research, we observed that each retrieval method had distinct **trade-offs in computational efficiency and accuracy**, making them suitable for different use cases:  

- **Vector Similarity Search** was **computationally lighter and faster**, making it ideal for broad similarity-based lookups.  
- **Knowledge Graph-Only Search** leveraged **structured relationships**, excelling at retrieving well-defined, explicit connections.  
- **Hybrid Search (Vector + Knowledge Graph)** provided **deeper contextual understanding** but required **higher computational costs** due to multiple retrieval steps.  
