"""
Dr. Martens AI Customer Support - Backend API with Anthropic Claude
Agentic AI powered by Claude for intelligent customer support
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import pandas as pd
import os
import json
from dotenv import load_dotenv
from anthropic import Anthropic

load_dotenv()

app = Flask(__name__)
CORS(app)

# =============================================================================
# ANTHROPIC CLIENT SETUP
# =============================================================================
client = Anthropic(api_key=os.getenv('ANTHROPIC_API_KEY'))

# =============================================================================
# LOAD REAL CUSTOMER DATA FROM CSV
# =============================================================================
def load_customer_data(csv_path=None):
    """Load customer reviews from CSV file"""
    
    possible_paths = [
        csv_path,
        'dr_martens_training_dataset_50.csv',
        '../dr_martens_training_dataset_50.csv',
        os.path.expanduser('~/dr-martens-project/dr_martens_training_dataset_50.csv'),
        os.path.expanduser('~/dr-martens-project/scraper/dr_martens_training_dataset_50.csv'),
        os.path.expanduser('~/dr-martens-project/drmartens-fullstack/backend/dr_martens_training_dataset_50.csv'),
    ]
    
    df = None
    loaded_path = None
    
    for path in possible_paths:
        if path and os.path.exists(path):
            try:
                df = pd.read_csv(path)
                loaded_path = path
                print(f"✅ Loaded {len(df)} customer records from: {path}")
                break
            except Exception as e:
                print(f"❌ Failed to load {path}: {e}")
    
    if df is None:
        print("⚠️  No CSV found.")
        return {}, None
    
    # Convert DataFrame to dictionary keyed by order_number
    customer_db = {}
    for _, row in df.iterrows():
        order_num = str(row['order_number']).upper()
        customer_db[order_num] = {
            'order_number': order_num,
            'star_rating': int(row['star_rating']) if pd.notna(row['star_rating']) else 1,
            'customer_name': str(row['customer_name']) if pd.notna(row['customer_name']) else 'Customer',
            'review_title': str(row['review_title']) if pd.notna(row['review_title']) else '',
            'review_text': str(row['review_text_full']) if pd.notna(row.get('review_text_full')) else str(row['review_text']) if pd.notna(row['review_text']) else '',
            'review_date': str(row['review_date']) if pd.notna(row['review_date']) else '',
            'product_name': str(row['product_name']) if pd.notna(row['product_name']) else 'Dr. Martens Product',
            'product_url': str(row['product_url']) if pd.notna(row.get('product_url')) else '',
            'issue_category': str(row['issue_category']) if pd.notna(row['issue_category']) else 'general',
            'action_required': str(row['action_required']) if pd.notna(row['action_required']) else 'knowledge_base',
            'priority_level': str(row['priority_level']) if pd.notna(row['priority_level']) else 'low',
            'suggested_resolution': str(row['suggested_resolution']) if pd.notna(row['suggested_resolution']) else 'Provide assistance',
            'integration_system': str(row['integration_system']) if pd.notna(row['integration_system']) else 'rag_knowledge',
            'escalation_needed': row['escalation_needed'] if pd.notna(row.get('escalation_needed')) else False,
            'sentiment': str(row['sentiment']) if pd.notna(row['sentiment']) else 'neutral',
        }
    
    return customer_db, loaded_path

# Load customer data on startup
customer_reviews_db, csv_source = load_customer_data()


# =============================================================================
# AGENT TOOLS - These are the actions Claude can take autonomously
# =============================================================================
AGENT_TOOLS = [
    {
        "name": "lookup_order",
        "description": "Look up customer information by order number. Use this when a customer provides their order number (format: DM followed by 8 digits, e.g., DM24382608).",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": "The order number starting with DM"
                }
            },
            "required": ["order_number"]
        }
    },
    {
        "name": "process_refund",
        "description": "Process a refund for a customer's order. Use this when a customer wants their money back.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": "The order number to refund"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for the refund"
                }
            },
            "required": ["order_number", "reason"]
        }
    },
    {
        "name": "initiate_repair",
        "description": "Initiate a repair request under the Dr. Martens 'For Life' warranty program. Use this when a product is damaged or defective.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": "The order number for the repair"
                },
                "issue_description": {
                    "type": "string",
                    "description": "Description of what needs to be repaired"
                }
            },
            "required": ["order_number", "issue_description"]
        }
    },
    {
        "name": "create_exchange",
        "description": "Create a size or product exchange. Use this when a customer needs a different size.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": "The order number to exchange"
                },
                "new_size": {
                    "type": "string",
                    "description": "The new size requested"
                },
                "reason": {
                    "type": "string",
                    "description": "Reason for exchange"
                }
            },
            "required": ["order_number", "reason"]
        }
    },
    {
        "name": "escalate_to_human",
        "description": "Escalate the case to a human support agent. Use this for complex issues, very angry customers, or when you cannot resolve the issue.",
        "input_schema": {
            "type": "object",
            "properties": {
                "order_number": {
                    "type": "string",
                    "description": "The order number if available"
                },
                "reason": {
                    "type": "string",
                    "description": "Why this needs human attention"
                },
                "priority": {
                    "type": "string",
                    "enum": ["low", "medium", "high", "critical"],
                    "description": "Priority level for escalation"
                }
            },
            "required": ["reason", "priority"]
        }
    },
    {
        "name": "book_appointment",
        "description": "Book an in-store appointment for fitting or consultation.",
        "input_schema": {
            "type": "object",
            "properties": {
                "customer_name": {
                    "type": "string",
                    "description": "Customer's name"
                },
                "preferred_date": {
                    "type": "string",
                    "description": "Preferred appointment date"
                },
                "store_location": {
                    "type": "string",
                    "description": "Preferred store location"
                }
            },
            "required": ["customer_name"]
        }
    }
]


# =============================================================================
# TOOL EXECUTION FUNCTIONS
# =============================================================================
def execute_tool(tool_name: str, tool_input: dict) -> dict:
    """Execute an agent tool and return the result"""
    
    if tool_name == "lookup_order":
        order_number = tool_input.get("order_number", "").upper()
        if order_number in customer_reviews_db:
            customer = customer_reviews_db[order_number]
            return {
                "success": True,
                "customer": customer,
                "message": f"Found customer {customer['customer_name']} with order {order_number}"
            }
        return {
            "success": False,
            "message": f"Order {order_number} not found in system",
            "available_sample": list(customer_reviews_db.keys())[:5]
        }
    
    elif tool_name == "process_refund":
        order_number = tool_input.get("order_number", "").upper()
        reason = tool_input.get("reason", "Customer request")
        customer = customer_reviews_db.get(order_number, {})
        return {
            "success": True,
            "action": "refund_processed",
            "refund_id": f"REF-{order_number}",
            "amount": "$189.00",
            "product": customer.get("product_name", "Dr. Martens Product"),
            "method": "Original payment method",
            "estimated_time": "3-5 business days",
            "discount_code": "SORRY15",
            "discount_value": "15% off next order",
            "message": f"Refund processed for order {order_number}. Reason: {reason}"
        }
    
    elif tool_name == "initiate_repair":
        order_number = tool_input.get("order_number", "").upper()
        issue = tool_input.get("issue_description", "Product defect")
        customer = customer_reviews_db.get(order_number, {})
        return {
            "success": True,
            "action": "repair_initiated",
            "repair_id": f"REPAIR-{order_number}",
            "product": customer.get("product_name", "Dr. Martens Product"),
            "issue": issue,
            "shipping_label": "Prepaid label sent to customer email",
            "tracking": f"DMREP{order_number[-6:]}",
            "estimated_time": "2-3 weeks",
            "warranty": "Covered under For Life warranty",
            "message": f"Repair initiated for {customer.get('product_name', 'product')}. Issue: {issue}"
        }
    
    elif tool_name == "create_exchange":
        order_number = tool_input.get("order_number", "").upper()
        new_size = tool_input.get("new_size", "TBD")
        reason = tool_input.get("reason", "Size exchange")
        customer = customer_reviews_db.get(order_number, {})
        return {
            "success": True,
            "action": "exchange_created",
            "exchange_id": f"EXC-{order_number}",
            "product": customer.get("product_name", "Dr. Martens Product"),
            "new_size": new_size,
            "shipping": "Expedited 2-3 days",
            "return_label": "Sent to customer email",
            "message": f"Exchange created for order {order_number}. New size: {new_size}"
        }
    
    elif tool_name == "escalate_to_human":
        order_number = tool_input.get("order_number", "N/A").upper()
        reason = tool_input.get("reason", "Complex issue")
        priority = tool_input.get("priority", "high")
        customer = customer_reviews_db.get(order_number, {})
        return {
            "success": True,
            "action": "escalated",
            "ticket_id": f"ESC-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            "customer": customer.get("customer_name", "Customer"),
            "priority": priority,
            "assigned_to": "Senior Support Team",
            "callback": "Within 2 hours" if priority in ["high", "critical"] else "Within 24 hours",
            "message": f"Case escalated to human agent. Priority: {priority}. Reason: {reason}"
        }
    
    elif tool_name == "book_appointment":
        customer_name = tool_input.get("customer_name", "Customer")
        preferred_date = tool_input.get("preferred_date", "Next available")
        store = tool_input.get("store_location", "Nearest store")
        return {
            "success": True,
            "action": "appointment_booked",
            "appointment_id": f"APT-{datetime.now().strftime('%Y%m%d%H%M')}",
            "customer": customer_name,
            "store": store,
            "available_slots": ["Tomorrow 10:00 AM", "Tomorrow 2:00 PM", "Day after 11:00 AM"],
            "message": f"Appointment request received for {customer_name} at {store}"
        }
    
    return {"success": False, "message": f"Unknown tool: {tool_name}"}


# =============================================================================
# CLAUDE AGENT - The main AI brain
# =============================================================================
SYSTEM_PROMPT = """You are an AI customer service agent for Dr. Martens, the iconic boot company. You have access to tools to help customers with their orders.

YOUR PERSONALITY:
- Friendly, empathetic, and professional
- You genuinely care about resolving customer issues
- You acknowledge frustration and apologize sincerely for problems
- You're proactive in offering solutions

YOUR CAPABILITIES (use tools when appropriate):
1. **lookup_order** - Look up customer details by order number (DM + 8 digits)
2. **process_refund** - Process refunds for dissatisfied customers
3. **initiate_repair** - Start warranty repairs under "For Life" program
4. **create_exchange** - Handle size exchanges
5. **escalate_to_human** - Escalate complex issues to human agents
6. **book_appointment** - Book in-store fitting appointments

WORKFLOW:
1. If customer provides an order number, ALWAYS use lookup_order first
2. Review their purchase history and any previous complaints
3. Based on the issue category and sentiment, take appropriate action
4. For 1-2 star reviews or very negative sentiment, be extra empathetic
5. Proactively offer solutions - don't wait for customers to ask

ISSUE HANDLING:
- **Repair issues** (broken, damaged, strap broke, sole separated): Use initiate_repair
- **Sizing issues** (too small, too big, uncomfortable): Use create_exchange
- **Refund requests** (want money back, returning): Use process_refund
- **Very angry customers** (1 star, customer_service complaints): Consider escalate_to_human
- **Quality concerns**: Offer replacement OR refund, consider escalation

IMPORTANT:
- Always address customers by name when known
- Reference their specific product and issue
- If sentiment is "very_negative" or star_rating is 1, be extra apologetic
- After using a tool, explain the result clearly to the customer
- Offer a discount code (SORRY15 for 15% off) when appropriate

Remember: You represent Dr. Martens' commitment to quality and customer satisfaction. Every interaction is an opportunity to turn a frustrated customer into a loyal fan."""


def run_agent(user_message: str, conversation_history: list = None, current_customer: dict = None) -> dict:
    """Run the Claude agent with tools"""
    
    if conversation_history is None:
        conversation_history = []
    
    # Build context about current customer if available
    context = ""
    if current_customer:
        context = f"""
CURRENT CUSTOMER CONTEXT:
- Name: {current_customer.get('customer_name')}
- Order: {current_customer.get('order_number')}
- Product: {current_customer.get('product_name')}
- Issue Category: {current_customer.get('issue_category')}
- Priority: {current_customer.get('priority_level')}
- Star Rating: {current_customer.get('star_rating')}/5
- Sentiment: {current_customer.get('sentiment')}
- Review: "{current_customer.get('review_text', '')[:500]}"
- Suggested Resolution: {current_customer.get('suggested_resolution')}
- Escalation Needed: {current_customer.get('escalation_needed')}

Use this context to provide personalized support.
"""
    
    # Add user message to history
    messages = conversation_history.copy()
    messages.append({"role": "user", "content": user_message})
    
    # Track tool uses and results
    tool_results = []
    final_response = ""
    
    # Agent loop - keep running until we get a final response
    max_iterations = 5
    for i in range(max_iterations):
        try:
            response = client.messages.create(
                model="claude-sonnet-4-20250514",
                max_tokens=1024,
                system=SYSTEM_PROMPT + context,
                tools=AGENT_TOOLS,
                messages=messages
            )
            
            # Check if Claude wants to use tools
            if response.stop_reason == "tool_use":
                # Process each tool use
                tool_use_blocks = [block for block in response.content if block.type == "tool_use"]
                tool_results_for_message = []
                
                for tool_use in tool_use_blocks:
                    tool_name = tool_use.name
                    tool_input = tool_use.input
                    
                    print(f"🔧 Agent using tool: {tool_name}")
                    print(f"   Input: {json.dumps(tool_input, indent=2)}")
                    
                    # Execute the tool
                    result = execute_tool(tool_name, tool_input)
                    tool_results.append({
                        "tool": tool_name,
                        "input": tool_input,
                        "result": result
                    })
                    
                    tool_results_for_message.append({
                        "type": "tool_result",
                        "tool_use_id": tool_use.id,
                        "content": json.dumps(result)
                    })
                    
                    print(f"   Result: {json.dumps(result, indent=2)}")
                
                # Add assistant's response and tool results to messages
                messages.append({"role": "assistant", "content": response.content})
                messages.append({"role": "user", "content": tool_results_for_message})
                
            else:
                # Claude is done - extract final text response
                for block in response.content:
                    if hasattr(block, 'text'):
                        final_response = block.text
                        break
                break
                
        except Exception as e:
            print(f"❌ Error in agent loop: {e}")
            final_response = "I apologize, but I'm experiencing technical difficulties. Please try again or contact our support team directly."
            break
    
    return {
        "response": final_response,
        "tool_results": tool_results,
        "conversation_history": messages
    }


# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    api_key_set = bool(os.getenv('ANTHROPIC_API_KEY'))
    return jsonify({
        'status': 'healthy',
        'service': 'Dr. Martens AI Support API (Claude Powered)',
        'anthropic_api': 'configured' if api_key_set else 'NOT CONFIGURED - Set ANTHROPIC_API_KEY',
        'data_source': csv_source or 'sample_data',
        'customers_loaded': len(customer_reviews_db)
    })


@app.route('/api/customers', methods=['GET'])
def list_customers():
    """List all customer order numbers"""
    return jsonify({
        'success': True,
        'count': len(customer_reviews_db),
        'order_numbers': list(customer_reviews_db.keys())
    })


@app.route('/api/customer/<order_number>', methods=['GET'])
def get_customer(order_number):
    """Lookup customer by order number"""
    order_number = order_number.upper()
    
    if order_number in customer_reviews_db:
        return jsonify({
            'success': True,
            'customer': customer_reviews_db[order_number]
        })
    
    return jsonify({
        'success': False,
        'error': 'Order not found',
        'message': f'No customer found with order number {order_number}'
    }), 404


@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint - Claude-powered agentic AI"""
    data = request.json
    message = data.get('message', '')
    order_number = data.get('order_number')
    conversation_history = data.get('conversation_history', [])
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Extract order number from message if not provided
    if not order_number:
        import re
        match = re.search(r'DM\d{7,10}', message, re.IGNORECASE)
        if match:
            order_number = match.group().upper()
    
    # Lookup customer for context
    customer = None
    if order_number:
        customer = customer_reviews_db.get(order_number.upper())
    
    # Run the Claude agent
    agent_result = run_agent(
        user_message=message,
        conversation_history=conversation_history,
        current_customer=customer
    )
    
    # Generate suggestions based on context
    suggestions = generate_suggestions(customer)
    
    return jsonify({
        'success': True,
        'response': agent_result['response'],
        'customer': customer,
        'tool_results': agent_result['tool_results'],
        'suggestions': suggestions,
        'requires_escalation': customer.get('escalation_needed', False) if customer else False
    })


@app.route('/api/action/<action_type>', methods=['POST'])
def execute_action(action_type):
    """Execute a specific agent action directly"""
    data = request.json
    order_number = data.get('order_number', '').upper()
    customer = customer_reviews_db.get(order_number, {})
    
    tool_input = {
        'order_number': order_number,
        'reason': data.get('reason', 'Customer request'),
        'new_size': data.get('new_size'),
        'issue_description': data.get('issue_description', customer.get('review_title', 'Product issue')),
        'customer_name': customer.get('customer_name', 'Customer'),
        'priority': data.get('priority', 'high')
    }
    
    action_map = {
        'refund': 'process_refund',
        'repair': 'initiate_repair',
        'exchange': 'create_exchange',
        'escalate': 'escalate_to_human',
        'appointment': 'book_appointment'
    }
    
    tool_name = action_map.get(action_type)
    if not tool_name:
        return jsonify({'error': f'Unknown action: {action_type}'}), 400
    
    result = execute_tool(tool_name, tool_input)
    return jsonify(result)


@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    """Get dashboard KPIs"""
    total = len(customer_reviews_db)
    
    if total > 0:
        escalation_count = sum(1 for c in customer_reviews_db.values() if c.get('escalation_needed'))
        critical_count = sum(1 for c in customer_reviews_db.values() if c.get('priority_level') == 'critical')
        high_count = sum(1 for c in customer_reviews_db.values() if c.get('priority_level') == 'high')
        auto_resolved = total - escalation_count
        
        # Category breakdown
        categories = {}
        for customer in customer_reviews_db.values():
            cat = customer.get('issue_category', 'general')
            categories[cat] = categories.get(cat, 0) + 1
        
        return jsonify({
            'success': True,
            'kpis': {
                'total_conversations': total * 25,
                'auto_resolved': auto_resolved * 20,
                'auto_resolution_rate': round((auto_resolved / total) * 100, 1),
                'avg_handle_time': 2.3,
                'escalation_rate': round((escalation_count / total) * 100, 1),
                'csat_score': 4.6,
                'today': {
                    'conversations': total,
                    'resolved': auto_resolved,
                    'pending': escalation_count,
                    'critical': critical_count,
                    'high_priority': high_count
                },
                'by_category': categories
            }
        })
    
    return jsonify({'success': True, 'kpis': {}})


def generate_suggestions(customer: dict) -> list:
    """Generate contextual suggestions based on customer data"""
    if not customer:
        return ['I need to return something', 'My boots are damaged', 'Sizing help']
    
    issue = customer.get('issue_category', '')
    suggestions_map = {
        'repair': ['Yes, start repair', 'How long will it take?', 'I want a replacement'],
        'sizing': ['Yes, process exchange', 'What sizes available?', 'I want a refund'],
        'refund': ['Yes, process refund', 'Can I exchange instead?', 'Speak to manager'],
        'quality': ['I want a replacement', 'Process refund', 'Speak to quality team'],
        'customer_service': ['That works, thank you', 'Speak to someone now', 'I want a refund'],
    }
    
    return suggestions_map.get(issue, ['Yes, please help', 'Tell me more', 'Speak to a person'])


# =============================================================================
# RUN SERVER
# =============================================================================
if __name__ == '__main__':
    print("\n" + "="*60)
    print("🥾 DR. MARTENS AI CUSTOMER SUPPORT API")
    print("   Powered by Anthropic Claude")
    print("="*60)
    print(f"📊 Loaded {len(customer_reviews_db)} customer records")
    if csv_source:
        print(f"📁 Data source: {csv_source}")
    
    api_key = os.getenv('ANTHROPIC_API_KEY')
    if api_key:
        print(f"🔑 Anthropic API: Configured ({api_key[:10]}...)")
    else:
        print("⚠️  WARNING: ANTHROPIC_API_KEY not set!")
        print("   Create a .env file with: ANTHROPIC_API_KEY=your_key_here")
    
    print(f"🔗 API running at: http://localhost:5000")
    print("="*60 + "\n")
    
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
