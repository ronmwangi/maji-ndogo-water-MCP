Maji Ndogo Water Crisis MCP Server 

A Model Context Protocol (MCP) server that lets Claude query a real water-crisis dataset directly — turning raw data into conversational, on-demand insights instead of static charts.

What this is

Maji Ndogo ("small water" in Swahili) is a fictional country used in an ALX/Explore AI data analytics course to teach real-world data skills: over 60,000 site visits recording water source type, condition, pollution levels, and population served across five provinces.

This project connects that dataset to Claude through MCP — an open protocol that lets an AI model call external tools to fetch live, real data instead of relying only on what it was trained on. Ask Claude a question in plain English, and it queries the actual SQLite database behind the scenes to answer it.

Why I built this

I wanted hands-on proof of AI fluency beyond "I used ChatGPT to write some code" — a working integration that shows I can design tools for an LLM to use, reason about a real dataset's schema, and debug a full stack from raw MySQL dump to a live AI-callable server.

Architecture
 You ask Claude a question
          │
          ▼
   Claude Desktop
          │  (MCP protocol, stdio)
          ▼
  Python MCP Server (server.py)
          │
          ▼
   SQLite database (maji_ndogo.db)
   converted from the original
   MySQL dump used in the course
Tools available
Tool	What it does
get_province_statistics	Water source breakdown and people served for one province
get_water_source_details	Full details for a single water source, including pollution data for wells
compare_provinces	Side-by-side comparison of two provinces, including broken-tap percentage
get_problem_areas	Ranks towns by number of people affected by broken taps or contaminated wells
search_water_data	Flexible search by province, town, and/or source type
analyze_water_access	Percentage breakdown of water access types, nationwide or per province
Example questions you can ask Claude
"Give me water statistics for Kilimani province."
"Compare Kilimani and Akatsi — which has worse broken tap rates?"
"What are the top 5 towns most affected by broken or contaminated water?"
"Find all rivers used as water sources in Sokoto."
"What percentage of people have access to a working home tap?"
Setup
Clone this repo and cd into it.
Create and activate a virtual environment:
   python -m venv venv
   venv\Scripts\activate      # Windows
Install dependencies:
   pip install "mcp[cli]"
The dataset (maji_ndogo.db) is included — it was converted from the original MySQL dump provided in the ALX Maji Ndogo course using a custom conversion script (convert_to_sqlite.py, also included).
Add the server to your Claude Desktop config (Settings → Developer → Edit Config):
json
   {
     "mcpServers": {
       "maji-ndogo-water": {
         "command": "FULL_PATH_TO\\venv\\Scripts\\python.exe",
         "args": ["FULL_PATH_TO\\server.py"]
       }
     }
   }
Restart Claude Desktop. Ask it a water-crisis question.

Dataset credit

Dataset and scenario from the ALX / Explore AI Academy "Maji Ndogo" data analytics course.

Author

Ron Mwangi — automation specialist & data analyst, Nairobi.