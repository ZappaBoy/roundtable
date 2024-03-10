import os.path
import os.path
import traceback

from langchain import hub
from langchain_community.chat_models import ChatOllama
from langchain_community.document_loaders import WebBaseLoader
from langchain_community.embeddings import LlamaCppEmbeddings
from langchain_community.vectorstores.chroma import Chroma
from langchain_core.output_parsers import JsonOutputParser, StrOutputParser
from langchain_core.prompts import PromptTemplate
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langgraph.graph import END, StateGraph

from roundtable.services.meeting.meeting_state import MeetingState
from roundtable.shared.utils.configurator import Configurator
from roundtable.shared.utils.logger import Logger

SUPERVISOR = 'Supervisor'
RESEARCHER = 'Researcher'
CODER = 'Coder'
FINISH = 'FINISH'

llm_model = 'mistral:instruct'

n_batch = 512

embedding = LlamaCppEmbeddings(
    # https://huggingface.co/TheBloke/Llama-2-7B-GGUF/blob/main/llama-2-7b.Q5_K_M.gguf
    model_path=os.path.join(os.path.dirname(__file__), "..", "..", "..", "models_resources",
                            "nomic-embed-text-v1.5.Q4_K_S.gguf"),
    n_batch=n_batch,
)

url = "https://lilianweng.github.io/posts/2023-06-23-agent/"
loader = WebBaseLoader(url)
docs = loader.load()
text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
    chunk_size=500, chunk_overlap=100
)
all_splits = text_splitter.split_documents(docs)

vectorstore = Chroma.from_documents(
    documents=all_splits,
    collection_name="rag-chroma",
    embedding=embedding,
)
retriever = vectorstore.as_retriever()


class Meeting:

    def __init__(self):
        self.logger = Logger()
        self.llm_model = Configurator.instance().get_llm_model()

        self.meeting_chain = None
        self.tool_executor = None
        self.agent_runnable = None
        self.retriever = None

    def build_team(self):

        workflow = StateGraph(MeetingState)

        # Define the nodes
        workflow.add_node("retrieve", self.retrieve)  # retrieve
        workflow.add_node("grade_documents", self.grade_documents)  # grade documents
        workflow.add_node("generate", self.generate)  # generate
        workflow.add_node("transform_query", self.transform_query)  # transform_query
        workflow.add_node("prepare_for_final_grade", self.prepare_for_final_grade)  # passthrough

        # Build graph
        workflow.set_entry_point("retrieve")
        workflow.add_edge("retrieve", "grade_documents")
        workflow.add_conditional_edges(
            "grade_documents",
            self.decide_to_generate,
            {
                "transform_query": "transform_query",
                "generate": "generate",
            },
        )
        workflow.add_edge("transform_query", "retrieve")
        workflow.add_conditional_edges(
            "generate",
            self.grade_generation_v_documents,
            {
                "supported": "prepare_for_final_grade",
                "not supported": "generate",
            },
        )
        workflow.add_conditional_edges(
            "prepare_for_final_grade",
            self.grade_generation_v_question,
            {
                "useful": END,
                "not useful": "transform_query",
            },
        )

        self.meeting_chain = workflow.compile()

    def start_meeting(self):
        self.logger.info("Meeting started")
        self.build_team()
        running = True
        while running:
            user_input = input("Enter text (press 'q' or ctrl-c to quit): ")
            if user_input.lower() == 'q':
                running = False
            try:
                inputs = {"keys": {"question": user_input}}
                for output in self.meeting_chain.stream(inputs, {"recursion_limit": 100}, ):
                    for key, value in output.items():
                        print(f"Node '{key}':")
                        # Optional: print full state at each node
                        # pprint.pprint(value["keys"], indent=2, width=80, depth=None)
                    print("\n---\n")
                # print(value['keys']['generation'])
            except Exception as e:
                self.logger.error(e)
                traceback.print_exc()
                print('Sorry, something goes wrong. Try with a different input')

        self.end_meeting()

    def end_meeting(self):
        self.logger.info("Meeting ended")

    def get_chain(self):
        if self.meeting_chain is None:
            self.build_team()
        return self.meeting_chain

    @staticmethod
    def retrieve(state):
        """
        Retrieve documents

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, documents, that contains retrieved documents
        """
        print("---RETRIEVE---")
        state_dict = state["keys"]
        question = state_dict["question"]
        documents = retriever.get_relevant_documents(question)
        return {"keys": {"documents": documents, "question": question}}

    @staticmethod
    def generate(state):
        """
        Generate answer

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): New key added to state, generation, that contains LLM generation
        """
        print("---GENERATE---")
        state_dict = state["keys"]
        question = state_dict["question"]
        documents = state_dict["documents"]

        # Prompt
        prompt = hub.pull("rlm/rag-prompt")

        # LLM
        llm = ChatOllama(model=llm_model, temperature=0)

        # Post-processing
        def format_docs(docs):
            return "\n\n".join(doc.page_content for doc in docs)

        # Chain
        rag_chain = prompt | llm | StrOutputParser()

        # Run
        generation = rag_chain.invoke({"context": documents, "question": question})
        return {
            "keys": {"documents": documents, "question": question, "generation": generation}
        }

    @staticmethod
    def grade_documents(state):
        """
        Determines whether the retrieved documents are relevant to the question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with relevant documents
        """

        print("---CHECK RELEVANCE---")
        state_dict = state["keys"]
        question = state_dict["question"]
        documents = state_dict["documents"]

        # LLM
        llm = ChatOllama(model=llm_model, format="json", temperature=0)

        # Prompt
        prompt = PromptTemplate(
            template="""You are a grader assessing relevance of a retrieved document to a user question. \n 
            Here is the retrieved document: \n\n {context} \n\n
            Here is the user question: {question} \n
            If the document contains keywords related to the user question, grade it as relevant. \n
            It does not need to be a stringent test. The goal is to filter out erroneous retrievals. \n
            Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
            Provide the binary score as a JSON with a single key 'score' and no premable or explaination.""",
            input_variables=["question", "context"],
        )

        # Chain
        chain = prompt | llm | JsonOutputParser()

        # Score
        filtered_docs = []
        for d in documents:
            score = chain.invoke(
                {
                    "question": question,
                    "context": d.page_content,
                }
            )
            grade = score["score"]
            if grade == "yes":
                print("---GRADE: DOCUMENT RELEVANT---")
                filtered_docs.append(d)
            else:
                print("---GRADE: DOCUMENT NOT RELEVANT---")
                continue

        return {"keys": {"documents": filtered_docs, "question": question}}

    @staticmethod
    def transform_query(state):
        """
        Transform the query to produce a better question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates question key with a re-phrased question
        """

        print("---TRANSFORM QUERY---")
        state_dict = state["keys"]
        question = state_dict["question"]
        documents = state_dict["documents"]

        # LLM
        llm = ChatOllama(model=llm_model, temperature=0)

        # Create a prompt template with format instructions and the query
        prompt = PromptTemplate(
            template="""You are generating questions that is well optimized for retrieval. \n 
            Look at the input and try to reason about the underlying sematic intent / meaning. \n 
            Here is the initial question:
            \n ------- \n
            {question} 
            \n ------- \n
            Formulate an improved question:""",
            input_variables=["question"],
        )

        # Chain
        chain = prompt | llm | StrOutputParser()
        better_question = chain.invoke({"question": question})

        return {"keys": {"documents": documents, "question": better_question}}

    @staticmethod
    def prepare_for_final_grade(state):
        """
        Passthrough state for final grade.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): The current graph state
        """

        print("---FINAL GRADE---")
        state_dict = state["keys"]
        question = state_dict["question"]
        documents = state_dict["documents"]
        generation = state_dict["generation"]

        return {
            "keys": {"documents": documents, "question": question, "generation": generation}
        }

    @staticmethod
    def decide_to_generate(state):
        """
        Determines whether to generate an answer, or re-generate a question.

        Args:
            state (dict): The current state of the agent, including all keys.

        Returns:
            str: Next node to call
        """

        print("---DECIDE TO GENERATE---")
        state_dict = state["keys"]
        question = state_dict["question"]
        filtered_documents = state_dict["documents"]

        if not filtered_documents:
            # All documents have been filtered check_relevance
            # We will re-generate a new query
            print("---DECISION: TRANSFORM QUERY---")
            return "transform_query"
        else:
            # We have relevant documents, so generate answer
            print("---DECISION: GENERATE---")
            return "generate"

    @staticmethod
    def grade_generation_v_documents(state):
        """
        Determines whether the generation is grounded in the document.

        Args:
            state (dict): The current state of the agent, including all keys.

        Returns:
            str: Binary decision
        """

        print("---GRADE GENERATION vs DOCUMENTS---")
        state_dict = state["keys"]
        question = state_dict["question"]
        documents = state_dict["documents"]
        generation = state_dict["generation"]

        # LLM
        llm = ChatOllama(model=llm_model, format="json", temperature=0)

        # Prompt
        prompt = PromptTemplate(
            template="""You are a grader assessing whether an answer is grounded in / supported by a set of facts. \n 
            Here are the facts:
            \n ------- \n
            {documents} 
            \n ------- \n
            Here is the answer: {generation}
            Give a binary score 'yes' or 'no' score to indicate whether the answer is grounded in / supported by a set of facts. \n
            Provide the binary score as a JSON with a single key 'score' and no premable or explaination.""",
            input_variables=["generation", "documents"],
        )

        # Chain
        chain = prompt | llm | JsonOutputParser()
        score = chain.invoke({"generation": generation, "documents": documents})
        grade = score["score"]

        if grade == "yes":
            print("---DECISION: SUPPORTED, MOVE TO FINAL GRADE---")
            return "supported"
        else:
            print("---DECISION: NOT SUPPORTED, GENERATE AGAIN---")
            return "not supported"

    @staticmethod
    def grade_generation_v_question(state):
        """
        Determines whether the generation addresses the question.

        Args:
            state (dict): The current state of the agent, including all keys.

        Returns:
            str: Binary decision
        """

        print("---GRADE GENERATION vs QUESTION---")
        state_dict = state["keys"]
        question = state_dict["question"]
        documents = state_dict["documents"]
        generation = state_dict["generation"]

        llm = ChatOllama(model=llm_model, format="json", temperature=0)

        # Prompt
        prompt = PromptTemplate(
            template="""You are a grader assessing whether an answer is useful to resolve a question. \n 
            Here is the answer:
            \n ------- \n
            {generation} 
            \n ------- \n
            Here is the question: {question}
            Give a binary score 'yes' or 'no' to indicate whether the answer is useful to resolve a question. \n
            Provide the binary score as a JSON with a single key 'score' and no premable or explaination.""",
            input_variables=["generation", "question"],
        )

        # Prompt
        chain = prompt | llm | JsonOutputParser()
        score = chain.invoke({"generation": generation, "question": question})
        grade = score["score"]

        if grade == "yes":
            print("---DECISION: USEFUL---")
            return "useful"
        else:
            print("---DECISION: NOT USEFUL---")
            return "not useful"
