import glob
from ..config import settings
from langchain_community.vectorstores.neo4j_vector import Neo4jVector
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import TokenTextSplitter
from langchain_neo4j import Neo4jGraph
from langchain.schema import Document
from openai import OpenAI
from langchain.schema import Document
import glob
from langchain.text_splitter import CharacterTextSplitter

def define_chunks():
    try:
        # Get all text files in the directory
        raw_files = glob.glob(r"./app/data/*.txt")
        
        # Read the content of each file into raw_documents
        raw_documents = []
        for file in raw_files:
            with open(file, "r") as f:
                raw_documents.append(f.read())
        
        # Convert raw documents into Document objects with 'page_content'
        documents = [Document(page_content=doc) for doc in raw_documents]
        
        # Chunking strategy: Each chunk will have at most 1000 characters
        # 20 characters will overlap between chunks to add context
        text_splitter = TokenTextSplitter(chunk_size=1000, chunk_overlap=20)

        # Split the documents into chunks
        files = text_splitter.split_documents(documents)
        print("len of doc is ", len(raw_documents[0]))
        print("files is ", len(files))
        # Optionally remove the "summary" metadata if it exists
        for i in files:
            if "summary" in i.metadata:
                del i.metadata["summary"]
        
        return files

    except Exception as e:
        return {"define_chunks error": str(e)}


def setup_indices(graph : Neo4jGraph):
    # Ensure full-text index for Chunk text exists
    try:
        existing_text_index = graph.query("SHOW INDEXES YIELD name WHERE name = 'my_chunk_text_index' RETURN name")
        if not existing_text_index:
            graph.query(
                "CALL db.index.fulltext.createNodeIndex('my_chunk_text_index', ['Chunk'], ['text']);"
            )

        # Check if vector index already exists
        existing_vector_index = graph.query("SHOW INDEXES YIELD name WHERE name = 'my_chunk_vector_index' RETURN name")
        if not existing_vector_index:
            graph.query(
                """
                CREATE VECTOR INDEX my_chunk_vector_index
                FOR (n:Chunk)
                ON (n.vector)
                OPTIONS {
                    indexConfig: {
                        `vector.dimensions`: 1536,
                        `vector.similarity_function`: 'cosine'
                    }
                };
                """
            )
    except Exception as e:
        return {"define_graph error": str(e)}



def define_graph():
    print("line 78")
    graph = Neo4jGraph(url = settings.p_neo4j_uri, username = settings.p_neo4j_user, password = settings.p_neo4j_password)
    print("line 80")
    embeddings = OpenAIEmbeddings(
        api_key=settings.openai_api_key
    )
    print("line 84")
    #setup_indices(graph)
    documents = define_chunks()  # This should already return Document objects

        # Check if documents are indeed Document objects
    print("line 89")
    if not all(isinstance(doc, Document) for doc in documents):
        raise TypeError("All documents must be instances of the Document class")
    try:
        neo4j_db = Neo4jVector.from_documents(
            documents = documents,
            embedding = embeddings,
            url = settings.p_neo4j_uri,
            username = settings.p_neo4j_user,
            password = settings.p_neo4j_password,
            database = "neo4j",
            index_name = "Transcript", #Node label is Transcript
            text_node_property = "info", #info property is used to store text
            embedding_node_property = "vector", #vector property hold the text embedding representation
            create_id_index = True,
        )
        print("line 105")
        return {
            "message": "Success"
        }

    except Exception as e:
        return {"define_graph error": str(e)}

def perform_search(query: str, k: int = 1):
    try:
        # Initialize the vector store
        embeddings = OpenAIEmbeddings(
        api_key=settings.openai_api_key
    )
        neo4j_db = Neo4jVector.from_existing_index(
            embedding=embeddings,
            url=settings.p_neo4j_uri,
            username=settings.p_neo4j_user,
            password=settings.p_neo4j_password,
            database="neo4j",
            index_name="Transcript",  # The same index name used when creating the vector store
            text_node_property="info",
        )

        print(f"Performing similarity search with query: {query}")
        results = neo4j_db.similarity_search(query, k=k)
        
       
        return answer_question(results, query)
        
    except Exception as e:
        print(f"Error performing search: {e}")


def answer_question(results, query):
    try:
        client = OpenAI(api_key= settings.openai_api_key)
        final_prompt = f"""You are an assistant that helps to form nice and human understandable answers.
            Given the user's query {query} and the information {results} provide a meaningful and efficient answer.
            The provided information is authoritative, you must never doubt it or try to use your internal knowledge to correct it.
            Make the answer sound as a response to the question. Do not mention that you based the result on the given information.
            If the provided information is empty, say that you don't know the answer.
            Final answer should be easily readable and structured.
            Information:"""
        chat_completion = client.chat.completions.create(messages=[{"role": "user","content": final_prompt,  }],model="gpt-4o-mini",)

        answer = chat_completion.choices[0].message.content.strip()
        return answer
    except Exception as e:
        print(f"Error answering question: {e}")

    

