from walledai import WalledProtect
import os
import pandas as pd
from datetime import datetime

# Use environment variable for security
API_KEY = "68cd7327baf96fe8cbefe631.d3af82e516541e7345bc6659606b5939" # Set with: export WALLED_AI_KEY="your_key"
print("Debug: Retrieved API_KEY =", repr(API_KEY))  # Add this line for debugging
if not API_KEY:
    raise ValueError("Set WALLED_AI_KEY environment variable!")

client = WalledProtect(api_key=API_KEY)

# Debug: Print available methods on client (run once to see, then comment out)
print("Available methods on WalledProtect client:", [m for m in dir(client) if not m.startswith('_')])

def moderate_comment(comment: str) -> dict:
    """
    Moderates comment with WalledProtect using the 'guard' method.
    Returns: {'safe': bool, 'reason': str, 'confidence': float, 'timestamp': str}
    """
    try:
        result = client.guard(text=comment)
        print("API Response:", result)  # Temporary: Remove after confirming
        
        # Parse nested structure from response
        safety_data = result['data']['safety'][0] if result['data']['safety'] else {}
        is_safe = safety_data.get('isSafe', True)
        score = safety_data.get('score', 0.0) if is_safe else safety_data.get('score', 1.0)
        safety_type = safety_data.get('safety', 'generic')
        method = safety_data.get('method', 'unknown')
        
        return {
            'safe': is_safe,
            'reason': f"{safety_type} ({method})",  # e.g., "generic (en-safety)"
            'confidence': float(score) if score is not None else 0.0,
            'timestamp': datetime.now().isoformat()
        }
    except (KeyError, IndexError) as e:
        print(f"Response Parse Error: {e}. Using default safe.")
        return {'safe': True, 'reason': 'parse_error', 'confidence': 0.0, 'timestamp': datetime.now().isoformat()}
    except AttributeError as e:
        print(f"SDK Method Error: {e}")
        return {'safe': True, 'reason': 'method_error', 'confidence': 0.0, 'timestamp': datetime.now().isoformat()}
    except Exception as e:
        print(f"API Error: {e}")
        return {'safe': True, 'reason': 'api_error', 'confidence': 0.0, 'timestamp': datetime.now().isoformat()}
# Simple in-memory storage for comments (use st.session_state in app for persistence)
SAFE_COMMENTS = pd.DataFrame(columns=['comment', 'safe', 'reason', 'confidence', 'timestamp'])
MODERATOR_QUEUE = pd.DataFrame(columns=['comment', 'safe', 'reason', 'confidence', 'timestamp', 'approved'])

# Remove the global SAFE_COMMENTS and MODERATOR_QUEUE lines (if present)

def add_safe_comment(result: dict, comment: str, safe_df: pd.DataFrame) -> pd.DataFrame:
    new_row = pd.DataFrame([{'comment': comment, **result}])
    if safe_df.empty:
        return new_row
    else:
        return pd.concat([safe_df, new_row], ignore_index=True)

def add_to_queue(result: dict, comment: str, queue_df: pd.DataFrame) -> pd.DataFrame:
    new_row = pd.DataFrame([{'comment': comment, **result, 'approved': False}])
    if queue_df.empty:
        return new_row
    else:
        return pd.concat([queue_df, new_row], ignore_index=True)

def approve_comment(index: int, queue_df: pd.DataFrame, safe_df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    if index < len(queue_df):
        queue_df.at[index, 'approved'] = True
        approved = queue_df.iloc[index].to_dict()
        safe_df = add_safe_comment(approved, approved['comment'], safe_df)
        queue_df = queue_df.drop(index).reset_index(drop=True)
        return queue_df, safe_df
    return queue_df, safe_df  # No change if invalid index

# Fallback: Raw HTTP if SDK method fails (uncomment if needed)
# import requests
# def moderate_comment_http(comment: str) -> dict:
#     url = "https://api.walled.ai/v1/classify"  # Check your dashboard for exact endpoint
#     headers = {"Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"}
#     data = {"text": comment}
#     try:
#         response = requests.post(url, json=data, headers=headers)
#         response.raise_for_status()
#         result = response.json()
#         return {
#             'safe': result.get('safe', True),
#             'reason': result.get('category', 'none'),
#             'confidence': result.get('score', 0.0),
#             'timestamp': datetime.now().isoformat()
#         }
#     except Exception as e:
#         print(f"HTTP API Error: {e}")
#         return {'safe': True