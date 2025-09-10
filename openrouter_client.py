import requests
import json
import logging
import os

class OpenRouterClient:
    def __init__(self, api_key=None):
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.base_url = "https://openrouter.ai/api/v1"
        # Get the current domain for production deployment
        referer_url = os.getenv("REPLIT_DOMAIN")
        if referer_url and not referer_url.startswith(('http://', 'https://')):
            referer_url = f"https://{referer_url}"
        
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "X-Title": "OpenRouter Chat Assistant"
        }
        
        # Only add HTTP-Referer if we have a valid domain
        if referer_url:
            self.headers["HTTP-Referer"] = referer_url
    
    def chat_completion(self, model, prompt, max_tokens=1000, temperature=0.7):
        """
        Send a chat completion request to OpenRouter
        """
        try:
            url = f"{self.base_url}/chat/completions"
            
            payload = {
                "model": model,
                "messages": [
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "max_tokens": max_tokens,
                "temperature": temperature
            }
            
            response = requests.post(url, headers=self.headers, json=payload, timeout=15)
            response.raise_for_status()
            
            data = response.json()
            
            if 'choices' in data and len(data['choices']) > 0:
                return {
                    'content': data['choices'][0]['message']['content'],
                    'model': data.get('model', model),
                    'usage': data.get('usage', {}),
                    'raw_response': data
                }
            else:
                raise Exception("No response content received from API")
                
        except requests.exceptions.RequestException as e:
            logging.error(f"OpenRouter API request error: {str(e)}")
            raise Exception(f"API request failed: {str(e)}")
        except Exception as e:
            logging.error(f"OpenRouter API error: {str(e)}")
            raise
    
    def get_models(self):
        """
        Get available models from OpenRouter
        """
        try:
            url = f"{self.base_url}/models"
            response = requests.get(url, headers=self.headers, timeout=30)
            response.raise_for_status()
            
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logging.error(f"OpenRouter models request error: {str(e)}")
            raise Exception(f"Failed to fetch models: {str(e)}")
        except Exception as e:
            logging.error(f"OpenRouter models error: {str(e)}")
            raise
