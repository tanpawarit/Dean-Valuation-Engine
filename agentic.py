import os
import re
from typing import TypedDict, List, Dict, Optional
from langgraph.graph import StateGraph, END
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import JsonOutputParser
import json
from datetime import datetime
from src.tools.search_tools import search_tool # Assuming this is correctly defined elsewhere
from src.utils import Config # Assuming this is correctly defined elsewhere
from langchain.chat_models import init_chat_model # Assuming this is correctly defined elsewhere

from langchain.agents import AgentExecutor, create_openai_functions_agent
from langchain.memory import ConversationBufferWindowMemory

all_configs = Config().get_config()

os.environ["OPENAI_API_KEY"] = all_configs['openai']['token']
if all_configs['serper']['token']:
    os.environ["SERPER_API_KEY"] = all_configs['serper']['token']

# Definition of business_analyst_agent (remains the same as in File 1)
def business_analyst_agent(task_detail: str) -> str:
    template_str = (
        '''   
        You are **Business Analyst** expert in business-model and market-sizing analysis.   
        If you are not sure about any detail in the data sources, **use your tools** to fetch or read the latest data and do NOT guess or make up facts.  
        You **MUST plan extensively** before each section of your analysis, and reflect on outcomes of any tool call before moving on.  

        Date: {current_date}
    
        # Core Business Model  
        - **Products/Services:** Briefly describe what the company sells or provides (apps, platforms, financial services, logistics, etc.).  
        - **Business Model Type:** Classify as Marketplace, B2B SaaS, D2C, Subscription-based, On-demand, etc.  
        - **Analyst Commentary:** Explain why this model makes the company competitive or where risks lie. 

        # Revenue Breakdown  
        - List each major product/service line with its **% of total revenue**.  
        - **Analyst Commentary:** Discuss what this mix means for growth prospects and margin stability.

        # Revenue Consistency  
        - Is revenue **cyclical** or **recurring**?  
        - Are there any **seasonal** or **economic-cycle** dependencies?  
        - **Analyst Commentary:** Evaluate how these patterns impact valuation and forecasting.

        # Business Category  
        - Classify as **Growth** (high-expansion, e.g. EV, AI, Healthtech) or **Defensive** (stable, e.g. Utilities, Consumer Staples).  
        - **Analyst Commentary:** Justify the classification and its implications for portfolio allocation.
    
        # Market Sizing Analysis
        - **TAM (Total Addressable Market):** Describe the total market demand your company could serve if there were no constraints on reach or resources.
        - **SAM (Serviceable Available Market):** Define the portion of the TAM that your company can realistically serve today given its current capabilities and geographic reach.
        - **SOM (Serviceable Obtainable Market):** State the share of the SAM that your company is currently capturing.

        if High SOM:
        - **Expansion Opportunities:** Identify adjacent customer segments or new geographies (e.g., international markets, verticals) you could pursue to grow share.
        - **Analyst Commentary:** Explain why these expansion moves make strategic sense and what resources or partnerships would be required.

        if Low SOM:
        - **Growth Potential:** Assess your competitive advantages (e.g., technology, pricing, brand) and latent market demand to project potential share gains.
        - **Analyst Commentary:** Discuss which levers (marketing, product features, distribution) will drive that growth.
    
        ## Content Guidelines:
        ### Required Information:
        - Annual Reports (10-K, 56-1)
        - Analyst Reports (Equity Research)
        - Latest Investor Presentation
        - Quarterly revenue compared to economic cycles
        - Market size data from reference sources such as McKinsey, Statista, and Gartner
        - Market share figures from industry reports
        - Reports from competitors within the same industry
        
        ### Depth and Breadth:
        - Aim for comprehensive coverage of each subsection  
        - Include definitions of key terms and concepts  
        - Discuss current understanding and applications  
        - Address relationships between different concepts  
        - Add citations and link

        ### Structure:
        - Use hierarchical formatting with clear headings  
        - Use paragraphs to organize information logically  
        - Include transitional phrases between subsections  
        - no intro and conclusion

        ### Content Quality:
        - Prioritize accuracy and clarity  
        - Provide specific examples to illustrate concepts  
        - Include relevant data points, statistics, or findings when applicable  
        - Maintain an objective, scholarly tone  
        - Avoid oversimplification of topics  

        **Use only the most up-to-date sources as of {current_date}:** **Output only the 4 sections—no intros, no conclusions**
        '''
    )

    system_prompt = template_str.format(
        current_date=datetime.now().strftime("%Y-%m-%d")
    )

    model = init_chat_model(
        "openai:gpt-4.1", 
        temperature=0.1
    )

    memory = ConversationBufferWindowMemory(
        k=5, 
        memory_key="chat_history", 
        input_key="input",       
        output_key="output",     
        return_messages=True
    )

    agent_prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])

    tools = [search_tool] 
    
    agent = create_openai_functions_agent(llm=model, tools=tools, prompt=agent_prompt_template)

    business_analyst_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True, 
        handle_parsing_errors="An error occurred while parsing the agent's response. Please try rephrasing or check the output format.",
        name="business_analyst_executor",
        max_iterations=30, 
    )

    try:
        response_dict = business_analyst_executor.invoke({
            "input": task_detail
        })
        return response_dict.get('output', f"Business Analyst Agent did not produce a final output for: {task_detail}")
    except Exception as e:
        print(f"Error in Business Analyst Agent: {e}")
        return f"Error executing Business Analyst Agent: {e}"

# Definition of financial_strength_analyst_agent (remains the same as in File 1)
def financial_strength_analyst_agent(task_detail: str) -> str:
    template_str = (
        '''   
        You are **Fundamental Analyst** expert in Financial Strength Analysis.   
        If you are not sure about any detail in the data sources, **use your tools** to fetch or read the latest data and do NOT guess or make up facts.  
        You **MUST plan extensively** before each section of your analysis, and reflect on outcomes of any tool call before moving on.  

        Date: {current_date}
    
        # Financial Strength Analysis
        - **Debt-to-Equity (D/E)**
            - A **low value** is considered safer.
            - If **ROE is high but D/E is also high** $\rightarrow$ the company is using debt to generate profit, which indicates **risk**.
            - **Tech/SaaS** companies should ideally have a **D/E below 1**.
            - **Analyst Commentary:** Evaluate the company's D/E ratio against industry peers and historical trends. Discuss whether the current leverage is sustainable given the company's business model and growth stage. Highlight potential risks or advantages associated with its debt structure, especially if high ROE is driven by substantial debt.

        - **Current Ratio / Quick Ratio**
            - Measures the company's ability to **meet short-term obligations**.
            - An appropriate value is typically **> 1.2**.
                - **Retail** companies should have a higher ratio (due to significant inventory).
                - **SaaS** companies can have a lower ratio (as they typically have no inventory).
            - **Analyst Commentary:** Analyze the company's current and quick ratios, comparing them to industry averages and historical performance. Explain what these ratios indicate about the company's short-term liquidity position and its ability to cover immediate liabilities. Note any red flags or signs of strong liquidity.

        - **Free Cash Flow (FCF)**
            - More important than **accounting profit (EPS)**.
            - If **EPS grows but FCF does not** $\rightarrow$ indicates **low-quality earnings**.
            - **SaaS** companies should have **high FCF**; **Biotech or Startups** may not yet have positive FCF.
            - **Analyst Commentary:** Assess the company's FCF trends over time. Discuss the implications of FCF generation (or lack thereof) on the company's ability to fund operations, investments, debt repayment, and shareholder returns. If FCF diverges significantly from EPS growth, provide an in-depth explanation of the underlying reasons and the quality of earnings.

        - **FCF Margin = FCF / Revenue**
            - Measures the **quality of earnings in terms of cash flow**.
                - **SaaS** companies should ideally have an **FCF Margin > 20–30%**.
                - **Manufacturing** companies may have an **FCF Margin below 10%**.
            - **Analyst Commentary:** Analyze the company's FCF margin in the context of its industry and business model. Explain what this margin reveals about the efficiency with which the company converts revenue into free cash. Compare it to competitors and discuss whether it indicates a healthy, sustainable business or areas for operational improvement.
    
        ## Content Guidelines:
        ### Required Information:
        - Balance Sheet
        - Cash Flow Statement
        - Annual Reports (10-K, 56-1)
        - Industry benchmarks for comparison
        - Analyst Reports (Equity Research)
        - Latest Investor Presentation
        - Quarterly revenue compared to economic cycles

        ### Depth and Breadth:
        - Aim for comprehensive coverage of each subsection  
        - Include definitions of key terms and concepts  
        - Discuss current understanding and applications  
        - Address relationships between different concepts  
        - Add citations and link

        ### Structure:
        - Use hierarchical formatting with clear headings  
        - Use paragraphs to organize information logically  
        - Include transitional phrases between subsections  
        - no intro and conclusion

        ### Content Quality:
        - Prioritize accuracy and clarity  
        - Provide specific examples to illustrate concepts  
        - Include relevant data points, statistics, or findings when applicable  
        - Maintain an objective, scholarly tone  
        - Avoid oversimplification of topics  

        **Use only the most up-to-date sources as of {current_date}:** **Output only the 4 sections—no intros, no conclusions**
        '''
    )
    system_prompt = template_str.format(
        current_date=datetime.now().strftime("%Y-%m-%d")
    )
    model = init_chat_model("openai:gpt-4.1", temperature=0.1)
    memory = ConversationBufferWindowMemory(
        k=5, memory_key="chat_history", input_key="input", output_key="output", return_messages=True
    )
    agent_prompt_template = ChatPromptTemplate.from_messages([
        ("system", system_prompt),
        MessagesPlaceholder(variable_name="chat_history", optional=True),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    tools = [search_tool]
    agent = create_openai_functions_agent(llm=model, tools=tools, prompt=agent_prompt_template)
    financial_strength_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        memory=memory,
        verbose=True,
        handle_parsing_errors="Error parsing agent response. Please check format.",
        name="financial_strength_executor",
        max_iterations=30,
    )
    try:
        response_dict = financial_strength_executor.invoke({"input": task_detail})
        return response_dict.get('output', f"Financial Strength Agent did not produce a final output for: {task_detail}")
    except Exception as e:
        print(f"Error in Financial Strength Agent: {e}")
        return f"Error executing Financial Strength Agent: {e}"

AGENT_REGISTRY = {
    "Business Analyst Agent": business_analyst_agent,
    "Financial Strength Analyst Agent": financial_strength_analyst_agent,
}

# Definition of general_analyst_agent (remains the same as in File 1)
def general_analyst_agent(step_to_execute: str) -> str:
    general_llm = init_chat_model("openai:gpt-3.5-turbo", temperature=0.1)
    general_tools = [search_tool]
    current_date_str = datetime.now().strftime("%Y-%m-%d")
    general_react_prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            f"You are a helpful general-purpose assistant. Your task is to directly address and complete the human input. "
            f"If the input is a question, answer it. If it's an instruction, try to carry it out. "
            f"Use your available tools (like search) ONLY if it's clearly necessary to find external information to fulfill the request. "
            f"If the task seems like a meta-instruction (e.g., 'summarize previous findings', 'understand user input', 'prepare final response'), "
            f"provide a brief statement acknowledging the nature of the task and stating what you would do conceptually, but do not try to search for how to do it abstractly. "
            f"For example, if the task is 'Understand the user input: What is the capital of France?', respond with 'Acknowledged: Understand the user input. The core query is about the capital of France.' "
            f"If the task is a direct question like 'What is the capital of France?', then answer it (e.g. 'Paris'). "
            f"If the task is 'Search for the latest AI trends', then use the search tool. "
            f"Today's date is {current_date_str}."
        )),
        ("human", "{input}"),
        MessagesPlaceholder(variable_name="agent_scratchpad"),
    ])
    general_step_agent = create_openai_functions_agent(
        llm=general_llm,
        tools=general_tools,
        prompt=general_react_prompt_template
    )
    general_step_agent_executor = AgentExecutor(
        agent=general_step_agent,
        tools=general_tools,
        verbose=True,
        handle_parsing_errors="An error occurred while processing the general task step. Please check the input or tool usage.",
        name="general_step_executor",
        max_iterations=5,
    )
    agent_response = general_step_agent_executor.invoke({
        "input": step_to_execute
    })
    return agent_response.get('output', f"General React Agent did not produce a final output for: {step_to_execute}")

class PreActState(TypedDict):
    user_input: str
    current_plan: List[str]
    executed_steps_details: List[Dict[str, str]]
    current_step_index: int
    max_refinements: int
    refinement_count: int
    requires_refinement: bool
    error_message: Optional[str]
    final_response: Optional[str]

# --- NEW: Summarizer Agent Function ---
def summarizer_agent_function(user_input: str, executed_steps: List[Dict[str, str]]) -> str:
    print("---SUMMARIZER AGENT FUNCTION---")
    if not executed_steps:
        return "No steps were executed, so no summary can be provided."

    # Prepare the context for the summarizer LLM
    formatted_history = "\n".join([
        f"Step {i+1}: {details['step']}\nResult {i+1}: {str(details['result'])[:1000]}" # Truncate long results for summarizer
        for i, details in enumerate(executed_steps)
    ])

    summary_prompt_template = ChatPromptTemplate.from_messages([
        ("system", (
            "You are a summarization expert. Your task is to synthesize the outcomes of a multi-step plan into a coherent and comprehensive final response for the user. "
            "The user originally asked: '{user_input}'.\n\n"
            "The following steps were executed with their results:\n{execution_history}\n\n"
            "Based on all the information gathered and the original user request, provide a final, consolidated answer. "
            "Ensure the answer is easy to understand, directly addresses the user's query, and integrates key findings from the executed steps. "
            "Do not just list the results; synthesize them into a narrative or a structured response as appropriate."
            "If any step failed or an error occurred that is relevant to the final answer, acknowledge it if necessary but focus on providing the best possible answer with the available information."
        )),
        ("human", "Please provide the final consolidated answer.") # Placeholder for human input to the prompt
    ])

    summarizer_llm = ChatOpenAI(model="gpt-3.5-turbo-0125", temperature=0.2) # Or use GPT-4 for higher quality
    
    chain = summary_prompt_template | summarizer_llm


    try:
        summary = chain.invoke({
            "user_input": user_input,
            "execution_history": formatted_history
        })
        return summary
    except Exception as e:
        print(f"Summarizer Agent Error: {e}")
        return f"Error during summarization: {e}. Raw history: {formatted_history}"

# --- NEW: Summarizer Node ---
def summarizer_node(state: PreActState) -> PreActState:
    print("---SUMMARIZER NODE---")
    user_input = state["user_input"]
    executed_steps = state.get("executed_steps_details", [])
    
    if state.get("error_message") and not executed_steps: # If error occurred before any execution, skip summarizer
        print("Summarizer: Skipping due to pre-execution error.")
        # final_response might be set by response_generator for this case
        return state

    summary = summarizer_agent_function(user_input, executed_steps)
    state["final_response"] = summary
    # Potentially clear error_message if summarizer is expected to handle/incorporate it
    # state["error_message"] = None # Optional: if summary is comprehensive
    print(f"Summarizer: Final response generated.")
    return state

def planner_node(state: PreActState) -> PreActState:
    print("---PLANNER NODE (LLM Powered)---")
    user_input = state["user_input"]
    refinement_count = state["refinement_count"]

    if not os.getenv("OPENAI_API_KEY"):
        error_msg = "OPENAI_API_KEY is not set. Please ensure it is configured correctly."
        print(f"Planner Error: {error_msg}")
        state["error_message"] = error_msg
        state["current_plan"] = ["เกิดข้อผิดพลาด: ไม่ได้ตั้งค่า OPENAI_API_KEY"]
        state["final_response"] = f"เกิดข้อผิดพลาดในการวางแผน: {error_msg}" # Set final_response here for direct error
        state["current_step_index"] = 0
        state["requires_refinement"] = False
        return state

    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
    parser = JsonOutputParser()

    # MODIFIED PROMPT TEMPLATE for planner
    prompt_template_str = """
    คุณเป็น AI "Analyst Manager" ผู้เชี่ยวชาญในการวางแผนและมอบหมายงานต่อให้กับทีมเฉพาะทางอย่างมีประสิทธิภาพ
    เป้าหมายของคุณคือการวิเคราะห์คำสั่งของผู้ใช้ และสร้างแผนการทำงานที่เป็นขั้นตอนชัดเจน ซึ่งควรรวมถึงการพิจารณาว่าจะมอบหมายส่วนงานหลักให้ทีมใดทีมหนึ่ง (ถ้าจำเป็น) หรือจัดการเองหากเป็นคำถามง่ายๆ
    หลังจากทุกขั้นตอนในแผนงานของคุณเสร็จสิ้น จะมี Summarizer Agent มารวบรวมผลลัพธ์ทั้งหมดเพื่อสร้างคำตอบสุดท้ายให้ผู้ใช้ ดังนั้น แผนของคุณไม่ต้องรวมขั้นตอนการสรุปผลสุดท้ายเอง

    คำสั่งของผู้ใช้: {user_input}

    {refinement_instructions}

    ทีมเฉพาะทางที่คุณสามารถมอบหมายงานหลักไปให้ได้ ประกอบด้วย:
    1.  **Business Analyst Agent**: รับผิดชอบคำขอที่เกี่ยวข้องกับการดำเนินธุรกิจ, การวิเคราะห์ตลาด, การหาขนาดตลาด, กลยุทธ์ทางธุรกิจ, การวิเคราะห์ข้อมูลภายในองค์กรเพื่อปรับปรุงประสิทธิภาพ
    2.  **Financial Strength Analyst Agent**: รับผิดชอบคำขอที่เกี่ยวข้องกับการวิเคราะห์ปัจจัยพื้นฐานของหุ้นหรือสินทรัพย์, การประเมินมูลค่าบริษัท, แนวโน้มเศรษฐกิจที่มีผลต่อการลงทุน, การวิเคราะห์รายงานทางการเงิน

    โปรดสร้างแผนการทำงานที่เป็นขั้นตอน (step-by-step) โดยแต่ละขั้นตอนควรชัดเจนและเรียงลำดับอย่างเหมาะสม แผนของคุณควรพิจารณาสิ่งต่อไปนี้:
    * ขั้นตอนการทำความเข้าใจและวิเคราะห์คำสั่งของผู้ใช้
    * ขั้นตอนการประเมินว่าคำสั่งนั้นควรจัดการโดย agent ใด (Business Analyst Agent, Financial Strength Analyst Agent) หรือสามารถจัดการได้โดยตรง (general_analyst_agent สำหรับงานย่อยๆ)
    * หากมีการมอบหมายงานให้ agent เฉพาะทาง: ต้องมีขั้นตอน "มอบหมายงาน '[รายละเอียดงานย่อย]' ให้ [ชื่อ agent]" อย่างชัดเจน
    * (ถ้าจำเป็น) ขั้นตอนการรอรับผลลัพธ์จาก agent ที่ได้รับมอบหมาย (Planner ไม่ต้องสั่งให้ agent รวบรวมผลลัพธ์จาก agent อื่น)
    * **ข้อควรจำสำคัญสำหรับขั้นตอนทั่วไป (general_analyst_agent)**: หากขั้นตอนนี้ต้องการข้อมูลจากผลลัพธ์ของขั้นตอน *ก่อนหน้าโดยตรง* เพื่อดำเนินงานต่อ (ไม่ใช่การสรุปภาพรวมสุดท้าย) **คุณต้องสรุปหรืออ้างอิงข้อมูลที่จำเป็นนั้นใส่เข้าไปในคำอธิบายของขั้นตอนนั้นๆ อย่างชัดเจน** เนื่องจาก general_analyst_agent จะได้รับเฉพาะข้อความของขั้นตอนที่มันกำลังทำเท่านั้น และไม่มีสิทธิ์เข้าถึงประวัติการสนทนาหรือผลลัพธ์จากขั้นตอนอื่นโดยตรง ตัวอย่างเช่น แทนที่จะเขียนว่า "สรุปผลลัพธ์จากขั้นตอนที่แล้ว", ให้เขียนว่า "จากผลการวิเคราะห์ [ผลลัพธ์โดยย่อจากขั้นตอนที่แล้ว], ให้นำข้อมูลส่วน X มาจัดรูปแบบ"
    * แผนงานของคุณ *ไม่จำเป็นต้องมีขั้นตอนสุดท้ายสำหรับการสรุปภาพรวม* เพราะจะมี Summarizer Agent ทำหน้าที่นี้หลังจากทุกขั้นตอนในแผนของคุณดำเนินการเสร็จสิ้นแล้ว

    แผนของคุณต้องอยู่ในรูปแบบ JSON object ที่มี key เดียวคือ:
    1.  "plan": เป็น list ของ string ซึ่งแต่ละ string คือขั้นตอนการทำงาน จะมีกี่ขั้นตอนก็ได้ตามความเหมาะสม

    ตัวอย่าง JSON output สำหรับคำสั่ง "วิเคราะห์แนวโน้มตลาด e-commerce ในประเทศไทย และประเมินโอกาสทางธุรกิจ":
    {{
    "plan": [
        "ทำความเข้าใจคำสั่งผู้ใช้: 'วิเคราะห์แนวโน้มตลาด e-commerce ในประเทศไทย และประเมินโอกาสทางธุรกิจ'",
        "ประเมินว่าคำขอนี้เกี่ยวข้องกับการวิเคราะห์ตลาดและโอกาสทางธุรกิจ จึงเหมาะสมกับ Business Analyst Agent",
        "มอบหมายงาน 'วิเคราะห์แนวโน้มตลาด e-commerce ในไทยและประเมินโอกาส' ให้ Business Analyst Agent",
        "รอรับผลการวิเคราะห์ฉบับสมบูรณ์จาก Business Analyst Agent"
    ]
    }}
    (หลังจากนี้ Summarizer Agent จะทำงานต่อเพื่อสรุปผลจาก Business Analyst Agent)

    ตัวอย่าง JSON output สำหรับคำสั่ง "หุ้น XYZ น่าลงทุนระยะยาวหรือไม่ โปรดวิเคราะห์ปัจจัยพื้นฐาน และช่วยสรุปความเสี่ยงหลักๆ":
    {{
    "plan": [
        "ทำความเข้าใจคำสั่งผู้ใช้: 'หุ้น XYZ น่าลงทุนระยะยาวหรือไม่ โปรดวิเคราะห์ปัจจัยพื้นฐาน และช่วยสรุปความเสี่ยงหลักๆ'",
        "ประเมินว่าส่วนการวิเคราะห์ปัจจัยพื้นฐานเหมาะสมกับ Financial Strength Analyst Agent",
        "มอบหมายงาน 'วิเคราะห์ปัจจัยพื้นฐานหุ้น XYZ สำหรับการลงทุนระยะยาว และระบุความเสี่ยงหลัก' ให้ Financial Strength Analyst Agent",
        "รอรับผลการวิเคราะห์ปัจจัยพื้นฐานและความเสี่ยงจาก Financial Strength Analyst Agent"
    ]
    }}
    (หลังจากนี้ Summarizer Agent จะทำงานต่อเพื่อสรุปและนำเสนอความเสี่ยง)

    ตัวอย่าง JSON output สำหรับคำสั่ง "วันนี้วันอะไร":
    {{
    "plan": [
        "ทำความเข้าใจคำสั่งผู้ใช้: 'วันนี้วันอะไร'",
        "ประเมินว่าเป็นคำถามทั่วไป สามารถตอบได้โดยตรงโดย general_analyst_agent",
        "ตรวจสอบข้อมูลวันที่และเวลาปัจจุบันและแจ้งผู้ใช้"
        ]
    }}
    (ในกรณีนี้ อาจจะไม่จำเป็นต้องมี Summarizer Agent หาก general_analyst_agent ตอบได้สมบูรณ์แล้ว แต่โดยทั่วไป Summarizer Agent จะยังคงถูกเรียกเพื่อจัดรูปแบบคำตอบสุดท้ายหากมีผลลัพธ์จาก general_analyst_agent)

    JSON output ของคุณ:
    """
    refinement_instructions_str = ""
    if refinement_count > 0:
        print(f"Planner: Refining plan (attempt {refinement_count})")
        state["executed_steps_details"] = []

        error_info = state.get("error_message", "ไม่มีข้อมูลข้อผิดพลาดระบุ")
        refinement_instructions_str = f"""
            เกิดข้อผิดพลาดในการดำเนินการตามแผนเดิม: {error_info}
            โปรดพิจารณาข้อผิดพลาดนี้และสร้างแผนการทำงานใหม่หรือปรับปรุงแผนเดิมให้ดีขึ้นสำหรับคำสั่งผู้ใช้ตั้งต้น
        """
    else:
        print(f"Planner: Generating initial plan for input: '{user_input}'")
        state["executed_steps_details"] = []


    prompt = ChatPromptTemplate.from_template(prompt_template_str)
    chain = prompt | llm | parser

    try:
        print("Planner: Calling LLM to generate/refine plan...")
        llm_response = chain.invoke({
            "user_input": user_input,
            "refinement_instructions": refinement_instructions_str
        })
        print(f"Planner: LLM response received: {llm_response}")

        plan = llm_response.get("plan", [])

        if not plan or not isinstance(plan, list) or not all(isinstance(step, str) for step in plan) or len(plan) == 0:
            raise ValueError("LLM did not return a valid 'plan' list (it might be empty or incorrect format).")

        state["current_plan"] = plan
        state["error_message"] = None

    except Exception as e:
        print(f"Planner Error: Failed to get or parse plan from LLM. Error: {e}")
        state["error_message"] = f"LLM plan generation failed: {e}"
        state["current_plan"] = ["เกิดข้อผิดพลาดในการสร้างแผน"]
        state["final_response"] = f"เกิดข้อผิดพลาดในการสร้างแผน: {state['error_message']}" # Set final_response here

    state["current_step_index"] = 0
    state["requires_refinement"] = False
    print(f"Planner: New plan: {state.get('current_plan')}")
    return state

def executor_node(state: PreActState) -> PreActState:
    print("---EXECUTOR NODE---")
    current_plan = state.get("current_plan", [])
    current_step_index = state.get("current_step_index", 0)

    if not current_plan or current_step_index >= len(current_plan):
        print("Executor: No steps to execute or plan is empty/completed.")
        state["requires_refinement"] = False
        return state # Should proceed to summarizer or response_generator via conditional edge

    step_to_execute = current_plan[current_step_index]
    print(f"Executor: Executing step {current_step_index + 1}: '{step_to_execute}'")

    execution_successful = True
    step_result = "Not executed or no result captured" # Default value
    state["error_message"] = None
    state["requires_refinement"] = False

    agent_delegation_pattern = re.compile(r"มอบหมายงาน '(.*?)' ให้ (.*?(?:agent|Agent))")
    match = agent_delegation_pattern.search(step_to_execute)

    if match:
        task_detail_for_agent = match.group(1)
        agent_name_from_plan = match.group(2).strip()

        if agent_name_from_plan in AGENT_REGISTRY:
            agent_function = AGENT_REGISTRY[agent_name_from_plan]
            print(f"Executor: Delegating task '{task_detail_for_agent}' to agent: {agent_name_from_plan}")
            try:
                step_result = agent_function(task_detail_for_agent)
                print(f"Executor: Agent {agent_name_from_plan} completed.")
            except Exception as e:
                print(f"Executor: Agent {agent_name_from_plan} execution failed: {e}")
                step_result = f"การดำเนินการ Agent '{agent_name_from_plan}' ล้มเหลว: {e}"
                execution_successful = False
                state["error_message"] = step_result
                state["requires_refinement"] = True
        else:
            print(f"Executor: Agent '{agent_name_from_plan}' not found in AGENT_REGISTRY.")
            step_result = f"ไม่พบ Agent ชื่อ '{agent_name_from_plan}' ในระบบ"
            execution_successful = False
            state["error_message"] = step_result
            state["requires_refinement"] = True
    else:
        print(f"Executor: Step '{step_to_execute}' is not an agent delegation. Attempting to handle with general_analyst_agent.")
        try:
            step_result = general_analyst_agent(step_to_execute)
            print(f"Executor: General Analyst agent completed step. Result: {str(step_result)[:200]}...")
        except Exception as e:
            print(f"Executor: General Analyst agent execution failed for step '{step_to_execute}'. Error: {e}")
            step_result = f"การดำเนินการ General Analyst Agent ล้มเหลว: {e}"
            execution_successful = False
            state["error_message"] = f"การดำเนินการด้วย General Analyst agent ล้มเหลว: {e}" # Consistent error message
            state["requires_refinement"] = True

    if not execution_successful:
        print(f"Executor: Step failed. Error: {state.get('error_message', 'Unknown error')}")
    else:
        print(f"Executor: Step processed successfully.")

    executed_detail = {"step": step_to_execute, "result": step_result}
    if state.get("executed_steps_details") is None:
        state["executed_steps_details"] = []
    state["executed_steps_details"].append(executed_detail)

    if not state.get("requires_refinement", False):
        state["current_step_index"] += 1

    return state

# MODIFIED response_generator_node: Primarily for direct errors or if summarizer is skipped/fails
def response_generator_node(state: PreActState) -> PreActState:
    print("---RESPONSE GENERATOR NODE---")
    
    # If final_response is already set (e.g., by planner on critical failure, or by summarizer if it routes here on error), use it.
    if state.get("final_response"):
        print(f"Response Generator: Using pre-set final_response: {state['final_response']}")
        return state

    executed_steps = state.get("executed_steps_details", [])
    error_message = state.get("error_message")
    final_plan = state.get("current_plan", [])
    final_response_parts = []

    if error_message:
        final_response_parts.append(f"An error occurred: {error_message}")
        if executed_steps:
            final_response_parts.append("\nDetails of executed steps before error:")
            for detail in executed_steps:
                result_str = str(detail.get('result', 'N/A'))
                final_response_parts.append(f"- Step: {detail['step']}, Result: {result_str[:500]}")
        elif final_plan:
             final_response_parts.append("\nRelevant plan (if any):")
             for i, step in enumerate(final_plan):
                final_response_parts.append(f"- {step}")
    elif executed_steps: # Should ideally be handled by summarizer, but as a fallback
        final_response_parts.append("Execution completed. Results of steps:")
        for detail in executed_steps:
            result_str = str(detail.get('result', 'N/A'))
            final_response_parts.append(f"- Step: {detail['step']}, Result: {result_str[:500]}")
        final_response_parts.append("\n(Note: Summarization might have been skipped or failed.)")
    else:
        final_response_parts.append("No clear outcome or error to report.")
    
    state["final_response"] = "\n".join(final_response_parts)
    print(f"Response Generator: Final response generated: {state['final_response']}")
    return state

# MODIFIED should_refine_or_continue
def should_refine_or_continue(state: PreActState) -> str:
    print("---CONDITION: SHOULD REFINE OR CONTINUE?---")
    current_plan = state.get("current_plan", [])

    # Critical planner failure (e.g., API key) - already handled by planner's conditional edge now.
    # This node is primarily called after executor.

    if state.get("requires_refinement", False):
        if state.get("refinement_count", 0) < state.get("max_refinements", 0):
            new_refinement_count = state.get("refinement_count", 0) + 1
            state["refinement_count"] = new_refinement_count
            print(f"Decision: Needs refinement (attempt {new_refinement_count}). Routing to planner.")
            return "refine_plan"
        else:
            print("Decision: Max refinements reached. Routing to response_generator to report error.")
            state["error_message"] = (state.get("error_message", "An error occurred") + " (Max refinements reached)").strip()
            # state["final_response"] will be set by response_generator
            return "generate_response" # Error reporting path
    else:
        current_plan_len = len(current_plan)
        current_step_idx = state.get("current_step_index", 0)

        if current_step_idx < current_plan_len and current_plan_len > 0:
            print(f"Decision: Plan execution continues (step {current_step_idx + 1}/{current_plan_len}). Routing to executor.")
            return "continue_execution"
        else: # Plan completed
            if state.get("error_message"): # If plan completed but the last step resulted in an error not requiring refinement
                print(f"Decision: Plan completed but with a final error '{state.get('error_message')}'. Routing to response_generator.")
                return "generate_response" # Error reporting path
            else:
                print(f"Decision: Plan completed successfully. Routing to summarizer.")
                return "summarize_response" # Success path to new summarizer

# --- Graph Definition ---
workflow = StateGraph(PreActState)

workflow.add_node("planner", planner_node)
workflow.add_node("executor", executor_node)
workflow.add_node("summarizer", summarizer_node) # New node
workflow.add_node("response_generator", response_generator_node)

workflow.set_entry_point("planner")

# Edges from planner
workflow.add_conditional_edges(
    "planner",
    # If planner sets a critical error message in current_plan or directly sets final_response
    lambda state: "generate_response" if (state.get("current_plan") and \
                                         len(state.get("current_plan",[])) == 1 and \
                                         ("เกิดข้อผิดพลาดในการสร้างแผน" in state["current_plan"][0] or \
                                          "ไม่ได้ตั้งค่า OPENAI_API_KEY" in state["current_plan"][0])) or \
                                          (state.get("final_response") and "เกิดข้อผิดพลาดในการวางแผน" in state.get("final_response","")) \
                                     else "continue_to_executor",
    {
        "continue_to_executor": "executor",
        "generate_response": "response_generator" # For critical planner errors
    }
)

# Edges from executor
workflow.add_conditional_edges(
    "executor",
    should_refine_or_continue,
    {
        "refine_plan": "planner",
        "continue_execution": "executor",
        "summarize_response": "summarizer",         # New path for successful plan completion
        "generate_response": "response_generator"  # For errors after max refinements or unhandled errors
    }
)

workflow.add_edge("summarizer", END) # Summarizer sets final_response and ends
workflow.add_edge("response_generator", END) # Response_generator for error paths also ends

app = workflow.compile()

if __name__ == "__main__":
    print("เริ่มต้นการทำงานของ Pre-Act Agent (LLM Powered with Summarizer)...")

    if not os.getenv("OPENAI_API_KEY"):
        print("\n\n!!! คำเตือน: ไม่ได้ตั้งค่า OPENAI_API_KEY !!!")
        print("โปรดตั้งค่า OPENAI_API_KEY environment variable หรือในโค้ด (อย่างปลอดภัย) แล้วลองรันใหม่")

    test_case_1_input = "ตลาดหุ้นไทยวันนี้เป็นยังไงบ้าง แล้วช่วยสรุปข่าวเด่นๆ เกี่ยวกับเศรษฐกิจไทยให้หน่อย และวิเคราะห์ผลกระทบต่อ SET Index ด้วย"
    # test_case_1_input = "วางเเผนทริปทำบุญให้แอดนก"
    # test_case_1_input = "วิเคราะห์ปัจจัยพื้นฐานของหุ้น AAPL และสรุปแนวโน้มราคาในระยะสั้น"


    initial_state_test = {
        "user_input": test_case_1_input,
        "current_plan": [],
        "executed_steps_details": [],
        "current_step_index": 0,
        "max_refinements": 1,
        "refinement_count": 0,
        "requires_refinement": False,
        "error_message": None,
        "final_response": None
    }

    if os.getenv("OPENAI_API_KEY"):
        print(f"\n--- ทดสอบ Agent ด้วย Input: '{test_case_1_input}' ---")
        final_state_result = None # To store the final state from the last relevant event
        try:
            for event in app.stream(initial_state_test, config={'recursion_limit': 50}):
                for key, value in event.items():
                    print(f"Node: {key}")
                    # print(f"Value: {json.dumps(value, indent=2, ensure_ascii=False)}") # Can be very verbose
                    print("-" * 30)
                    # Capture the state from the last significant node before END
                    if key in ["summarizer", "response_generator", "planner"]: # planner if it errors out early
                        final_state_result = value

            if final_state_result and "final_response" in final_state_result and final_state_result["final_response"] is not None:
                print("\n--- ผลลัพธ์สุดท้าย (จาก State ล่าสุดใน Stream) ---")
                print(final_state_result["final_response"])
            else:
                print("\nStream เสร็จสิ้น, แต่ final_response ไม่ชัดเจนจาก stream events. ลอง invoke เพื่อดูผลลัพธ์...")
                # Invoking might be redundant if stream correctly captures the final state from summarizer/response_generator
                final_state_invoked = app.invoke(initial_state_test, config={'recursion_limit': 50})
                print("\n--- ผลลัพธ์สุดท้าย (จากการ invoke) ---")
                print(final_state_invoked.get("final_response", "ไม่มีคำตอบสุดท้ายแสดงผลจากการ invoke"))

        except Exception as e:
            print(f"\nเกิดข้อผิดพลาดระหว่างการรัน agent: {e}")
            import traceback
            traceback.print_exc()
    else:
        print("ไม่สามารถรันการทดสอบได้เนื่องจาก OPENAI_API_KEY ไม่ได้ถูกตั้งค่า")