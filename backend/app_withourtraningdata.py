"""
Dr. Martens AI Customer Support - Backend API
Flask server that connects the React frontend to the AI support system
"""

from flask import Flask, request, jsonify
from flask_cors import CORS
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
CORS(app)  # Enable CORS for React frontend

# =============================================================================
# SAMPLE CUSTOMER DATABASE (Replace with real CSV data or database)
# =============================================================================
customer_reviews_db = {
    "DM24210432": {
        "order_number": "DM24210432",
        "star_rating": 2,
        "customer_name": "Teresa Q.",
        "review_title": "THEY LOOK GREAT BUT ARE SO PAINFUL",
        "review_text": "Ordered my regular size 8 but these boots are extremely tight. After 3 weeks of trying to break them in, still can't wear them for more than an hour. Very disappointed for $200 boots. Need to return but past the window. Please help.",
        "review_date": "12/10/25",
        "product_name": "1460 Smooth Leather Boot",
        "issue_category": "sizing",
        "action_required": "exchange",
        "priority_level": "high",
        "suggested_resolution": "Free exchange for correct size with expedited shipping",
        "integration_system": "pos_inventory",
        "escalation_needed": False,
        "sentiment": "negative"
    },
    "DM24165432": {
        "order_number": "DM24165432",
        "star_rating": 1,
        "customer_name": "Marcus T.",
        "review_title": "SOLE SEPARATED AFTER 2 MONTHS",
        "review_text": "The sole completely detached from the boot. I barely wore them! This is unacceptable quality for the price. I want a full refund or replacement immediately. Dr. Martens used to be quality, what happened?",
        "review_date": "12/12/25",
        "product_name": "2976 Chelsea Boot",
        "issue_category": "repair",
        "action_required": "repair",
        "priority_level": "critical",
        "suggested_resolution": "Initiate For Life repair service + expedited replacement",
        "integration_system": "repair_flow",
        "escalation_needed": True,
        "sentiment": "very_negative"
    },
    "DM24276543": {
        "order_number": "DM24276543",
        "star_rating": 1,
        "customer_name": "Jennifer M.",
        "review_title": "WORST CUSTOMER SERVICE EXPERIENCE",
        "review_text": "Ordered boots 3 weeks ago, still not delivered. Customer service won't respond to emails or calls. Completely unacceptable. Want immediate refund.",
        "review_date": "12/18/25",
        "product_name": "2976 Chelsea Boot",
        "issue_category": "customer_service",
        "action_required": "escalate",
        "priority_level": "critical",
        "suggested_resolution": "Immediate manager callback + service recovery",
        "integration_system": "zendesk_escalation",
        "escalation_needed": True,
        "sentiment": "very_negative"
    },
    "DM24398765": {
        "order_number": "DM24398765",
        "star_rating": 3,
        "customer_name": "Sarah K.",
        "review_title": "Want to try before buying",
        "review_text": "Interested in the Jadon platform boots but unsure about sizing. Would like to try them on in store before ordering.",
        "review_date": "12/15/25",
        "product_name": "Jadon 8-Eye Boot",
        "issue_category": "appointment",
        "action_required": "appointment",
        "priority_level": "low",
        "suggested_resolution": "Book in-store fitting appointment with specialist",
        "integration_system": "pos_booking",
        "escalation_needed": False,
        "sentiment": "neutral"
    },
    "DM24232109": {
        "order_number": "DM24232109",
        "star_rating": 2,
        "customer_name": "Anyelic R.",
        "review_title": "Shipping disaster",
        "review_text": "Package arrived damaged and boots were scuffed. Paid for express shipping but took 2 weeks. Want refund for shipping at minimum.",
        "review_date": "12/20/25",
        "product_name": "1461 Oxford",
        "issue_category": "refund",
        "action_required": "refund",
        "priority_level": "high",
        "suggested_resolution": "Full shipping refund + 15% discount on next order",
        "integration_system": "shopify_returns",
        "escalation_needed": False,
        "sentiment": "negative"
    }
}

# =============================================================================
# ISSUE CLASSIFICATION ENGINE
# =============================================================================
class IssueClassifier:
    """Hybrid classification system - keyword triage + RAG for complex cases"""
    
    ISSUE_PATTERNS = {
        'refund': {
            'keywords': ['refund', 'money back', 'return', 'returning', 'reimburse'],
            'action': 'refund',
            'system': 'shopify_returns',
            'priority': 'high'
        },
        'repair': {
            'keywords': ['repair', 'broke', 'broken', 'sole', 'damaged', 'defect', 'separated', 'detached', 'ripped', 'torn'],
            'action': 'repair',
            'system': 'repair_flow',
            'priority': 'high'
        },
        'sizing': {
            'keywords': ['size', 'fit', 'tight', 'loose', 'small', 'large', 'uncomfortable', 'exchange'],
            'action': 'exchange',
            'system': 'pos_inventory',
            'priority': 'medium'
        },
        'quality': {
            'keywords': ['quality', 'cheap', 'poor', 'disappointing', 'color', 'faded'],
            'action': 'escalate',
            'system': 'zendesk_escalation',
            'priority': 'high'
        },
        'customer_service': {
            'keywords': ['customer service', 'support', 'no response', 'unhelpful', 'rude', 'manager', 'ignored'],
            'action': 'escalate',
            'system': 'zendesk_escalation',
            'priority': 'critical'
        },
        'shipping': {
            'keywords': ['shipping', 'delivery', 'late', 'delayed', 'lost', 'tracking', 'arrived damaged'],
            'action': 'investigate',
            'system': 'shipping_tracker',
            'priority': 'medium'
        },
        'appointment': {
            'keywords': ['appointment', 'store', 'try on', 'visit', 'fitting'],
            'action': 'appointment',
            'system': 'pos_booking',
            'priority': 'low'
        }
    }
    
    RESOLUTION_MAP = {
        'refund': 'Process full refund + 10% discount code for inconvenience',
        'repair': 'Initiate For Life repair service with prepaid shipping label',
        'exchange': 'Free size exchange with expedited shipping',
        'escalate': 'Escalate to senior support specialist for immediate attention',
        'investigate': 'Open shipping investigation + provide tracking update',
        'appointment': 'Book in-store fitting appointment with product specialist',
        'knowledge_base': 'Provide relevant information from knowledge base'
    }
    
    @classmethod
    def classify(cls, text: str) -> dict:
        """Classify customer issue from text"""
        text_lower = text.lower()
        
        for issue_type, pattern in cls.ISSUE_PATTERNS.items():
            if any(keyword in text_lower for keyword in pattern['keywords']):
                return {
                    'issue_type': issue_type,
                    'action': pattern['action'],
                    'system': pattern['system'],
                    'priority': pattern['priority'],
                    'suggested_resolution': cls.RESOLUTION_MAP.get(pattern['action'], 'Provide assistance')
                }
        
        # Default classification for general inquiries
        return {
            'issue_type': 'general',
            'action': 'knowledge_base',
            'system': 'rag_knowledge',
            'priority': 'low',
            'suggested_resolution': cls.RESOLUTION_MAP['knowledge_base']
        }


# =============================================================================
# AGENT ACTIONS (Mock implementations - connect to real systems in production)
# =============================================================================
class AgentActions:
    """Autonomous agent capabilities for customer support"""
    
    @staticmethod
    def process_refund(order_number: str, customer: dict) -> dict:
        """Process refund request"""
        return {
            'success': True,
            'action': 'refund_initiated',
            'message': f"Refund of $189.00 initiated for order {order_number}",
            'details': {
                'refund_id': f"REF-{order_number}",
                'amount': 189.00,
                'method': 'Original payment method',
                'estimated_time': '3-5 business days',
                'discount_code': 'SORRY15',
                'discount_value': '15% off next order'
            }
        }
    
    @staticmethod
    def initiate_repair(order_number: str, customer: dict) -> dict:
        """Initiate For Life repair service"""
        return {
            'success': True,
            'action': 'repair_initiated',
            'message': f"Repair request created for order {order_number}",
            'details': {
                'repair_id': f"REPAIR-{order_number}",
                'shipping_label': 'Sent to customer email',
                'estimated_repair_time': '2-3 weeks',
                'tracking_number': f"DM{order_number[-6:]}REP",
                'warranty_status': 'Covered under For Life warranty'
            }
        }
    
    @staticmethod
    def create_exchange(order_number: str, customer: dict, new_size: str = None) -> dict:
        """Create size exchange"""
        return {
            'success': True,
            'action': 'exchange_created',
            'message': f"Exchange initiated for order {order_number}",
            'details': {
                'exchange_id': f"EXC-{order_number}",
                'original_size': '8',
                'new_size': new_size or 'TBD - awaiting customer confirmation',
                'shipping': 'Expedited (2-3 days)',
                'return_label': 'Sent to customer email'
            }
        }
    
    @staticmethod
    def escalate_ticket(order_number: str, customer: dict, reason: str) -> dict:
        """Escalate to human agent"""
        return {
            'success': True,
            'action': 'escalated',
            'message': f"Case escalated to senior support for order {order_number}",
            'details': {
                'ticket_id': f"ESC-{order_number}",
                'priority': 'High',
                'assigned_to': 'Senior Support Team',
                'callback_scheduled': 'Within 2 hours',
                'reason': reason
            }
        }
    
    @staticmethod
    def book_appointment(customer: dict, store_location: str = None) -> dict:
        """Book store appointment"""
        return {
            'success': True,
            'action': 'appointment_booked',
            'message': "Store appointment request received",
            'details': {
                'appointment_id': f"APT-{datetime.now().strftime('%Y%m%d%H%M')}",
                'store': store_location or 'Nearest store - awaiting confirmation',
                'available_slots': [
                    'Tomorrow 10:00 AM',
                    'Tomorrow 2:00 PM',
                    'Day after tomorrow 11:00 AM'
                ],
                'specialist': 'Fit specialist will be assigned'
            }
        }


# =============================================================================
# API ROUTES
# =============================================================================

@app.route('/api/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'service': 'Dr. Martens AI Support API'})


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


@app.route('/api/classify', methods=['POST'])
def classify_issue():
    """Classify customer issue from message text"""
    data = request.json
    text = data.get('text', '')
    
    if not text:
        return jsonify({'error': 'No text provided'}), 400
    
    classification = IssueClassifier.classify(text)
    return jsonify({
        'success': True,
        'classification': classification
    })


@app.route('/api/chat', methods=['POST'])
def chat():
    """Main chat endpoint - processes customer messages and returns AI response"""
    data = request.json
    message = data.get('message', '')
    order_number = data.get('order_number')
    session_context = data.get('context', {})
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    # Extract order number from message if not provided
    if not order_number:
        import re
        match = re.search(r'DM\d{7,10}', message, re.IGNORECASE)
        if match:
            order_number = match.group().upper()
    
    # Lookup customer
    customer = None
    if order_number:
        customer = customer_reviews_db.get(order_number.upper())
    
    # Classify the issue
    classification = IssueClassifier.classify(message)
    
    # Generate response based on context
    response = generate_response(message, customer, classification, session_context)
    
    return jsonify({
        'success': True,
        'response': response['message'],
        'customer': customer,
        'classification': classification,
        'suggestions': response.get('suggestions', []),
        'action_taken': response.get('action_taken'),
        'requires_escalation': classification.get('priority') == 'critical'
    })


@app.route('/api/action/<action_type>', methods=['POST'])
def execute_action(action_type):
    """Execute agent action (refund, repair, exchange, escalate, appointment)"""
    data = request.json
    order_number = data.get('order_number', '').upper()
    customer = customer_reviews_db.get(order_number, {})
    
    action_map = {
        'refund': lambda: AgentActions.process_refund(order_number, customer),
        'repair': lambda: AgentActions.initiate_repair(order_number, customer),
        'exchange': lambda: AgentActions.create_exchange(order_number, customer, data.get('new_size')),
        'escalate': lambda: AgentActions.escalate_ticket(order_number, customer, data.get('reason', 'Customer request')),
        'appointment': lambda: AgentActions.book_appointment(customer, data.get('store_location'))
    }
    
    if action_type not in action_map:
        return jsonify({'error': f'Unknown action: {action_type}'}), 400
    
    result = action_map[action_type]()
    return jsonify(result)


@app.route('/api/kpis', methods=['GET'])
def get_kpis():
    """Get dashboard KPIs"""
    return jsonify({
        'success': True,
        'kpis': {
            'total_conversations': 1247,
            'auto_resolved': 892,
            'auto_resolution_rate': 71.5,
            'avg_handle_time': 2.3,
            'escalation_rate': 7.2,
            'csat_score': 4.6,
            'today': {
                'conversations': 45,
                'resolved': 38,
                'pending': 7
            }
        }
    })


# =============================================================================
# RESPONSE GENERATOR
# =============================================================================
def generate_response(message: str, customer: dict, classification: dict, context: dict) -> dict:
    """Generate contextual response based on customer data and classification"""
    
    # If we have customer context, personalize the response
    if customer:
        name = customer.get('customer_name', 'valued customer')
        issue = customer.get('issue_category', '')
        product = customer.get('product_name', 'your product')
        
        # Generate response based on issue type
        responses = {
            'sizing': {
                'message': f"Hi {name}! I can see you're having sizing issues with your {product}. I completely understand how frustrating it is when boots don't fit right. I can arrange a free size exchange with expedited shipping. Would you like me to process that for you?",
                'suggestions': ['Yes, process exchange', 'What sizes are available?', 'I want a refund instead']
            },
            'repair': {
                'message': f"Hi {name}, I'm so sorry to hear about the issue with your {product}. That's definitely not the quality you expect from Dr. Martens. Good news - your boots are covered under our 'For Life' warranty. I can initiate a repair right now and send you a prepaid shipping label. Shall I do that?",
                'suggestions': ['Yes, start repair', 'How long will repair take?', 'I want a replacement instead']
            },
            'refund': {
                'message': f"Hi {name}, I apologize for the trouble with your order. I can process a full refund for you right away, plus provide a 15% discount code for a future purchase. Would you like me to proceed?",
                'suggestions': ['Yes, process refund', 'Can I exchange instead?', 'Speak to a manager']
            },
            'customer_service': {
                'message': f"Hi {name}, I sincerely apologize for the poor experience you've had. This is not the level of service we strive for. I'm escalating your case to our senior support team immediately. You'll receive a callback within 2 hours. Is there anything else I can help with right now?",
                'suggestions': ['That works, thank you', 'I want to speak to someone now', 'I want a full refund']
            },
            'appointment': {
                'message': f"Hi {name}! I'd be happy to help you book a fitting appointment. We have slots available tomorrow at 10 AM, 2 PM, or the day after at 11 AM. A fit specialist will help you find your perfect size. Which time works best?",
                'suggestions': ['Tomorrow 10 AM', 'Tomorrow 2 PM', 'Day after tomorrow 11 AM']
            }
        }
        
        if issue in responses:
            return responses[issue]
        
        # Default personalized response
        return {
            'message': f"Hi {name}! Thank you for reaching out about your {product}. I'm here to help. Based on your concern, I suggest: {classification.get('suggested_resolution', 'Let me look into this for you.')} Would you like me to proceed?",
            'suggestions': ['Yes, please help', 'Tell me more', 'Speak to a person']
        }
    
    # No customer context - ask for order number
    issue_type = classification.get('issue_type', 'general')
    
    if issue_type != 'general':
        return {
            'message': f"I understand you're having a {issue_type.replace('_', ' ')} issue. To help you quickly, could you please provide your order number? It starts with 'DM' followed by numbers (e.g., DM24210432).",
            'suggestions': ['I have my order number', "I don't have it", 'General question']
        }
    
    return {
        'message': "Hello! I'm your Dr. Martens AI assistant. I can help with returns, repairs, exchanges, and store appointments. How can I help you today?",
        'suggestions': ['I need to return something', 'My boots are damaged', 'Book store appointment']
    }


# =============================================================================
# RUN SERVER
# =============================================================================
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
