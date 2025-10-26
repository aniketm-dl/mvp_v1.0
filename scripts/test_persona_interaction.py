#!/usr/bin/env python3
"""
Test Persona Interaction Script

This script allows you to interact with the trained personas to test
their behavior and responses.

Usage:
    python scripts/test_persona_interaction.py
    python scripts/test_persona_interaction.py --persona bargain_hunter
"""

from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
from typing import Dict, List, Any
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from peft import PeftModel

class PersonaTester:
    """Test interaction with trained personas."""
    
    def __init__(self, base_model: str = "mistralai/Mistral-7B-Instruct-v0.2"):
        self.base_model = base_model
        self.device = "cuda" if torch.cuda.is_available() else "cpu"
        self.tokenizer = None
        self.model = None
        self.personas = self._load_personas()
        
    def _load_personas(self) -> List[Dict[str, Any]]:
        """Load persona configurations."""
        personas_file = Path("DATA/personas.json")
        if not personas_file.exists():
            print("❌ Personas file not found. Please ensure DATA/personas.json exists.")
            return []
            
        with open(personas_file, 'r') as f:
            data = json.load(f)
        return data.get('personas', [])
    
    def _load_model_and_tokenizer(self):
        """Load the base model and tokenizer."""
        if self.tokenizer is None:
            print("🔄 Loading tokenizer...")
            self.tokenizer = AutoTokenizer.from_pretrained(self.base_model)
            if self.tokenizer.pad_token is None:
                self.tokenizer.pad_token = self.tokenizer.eos_token
                
        if self.model is None:
            print("🔄 Loading base model...")
            self.model = AutoModelForCausalLM.from_pretrained(
                self.base_model,
                torch_dtype=torch.float16 if self.device == "cuda" else torch.float32,
                device_map="auto" if self.device == "cuda" else None,
            )
    
    def load_persona_adapter(self, persona_id: str) -> bool:
        """Load a specific persona adapter."""
        adapter_path = Path(f"artifacts/llm_adapters/{persona_id}")
        
        if not adapter_path.exists():
            print(f"❌ Adapter not found: {adapter_path}")
            return False
            
        if not (adapter_path / "adapter_model.safetensors").exists():
            print(f"❌ Adapter model file not found in: {adapter_path}")
            return False
        
        try:
            print(f"🔄 Loading adapter for {persona_id}...")
            self.model = PeftModel.from_pretrained(self.model, str(adapter_path))
            print(f"✅ Loaded adapter for {persona_id}")
            return True
        except Exception as e:
            print(f"❌ Failed to load adapter: {e}")
            return False
    
    def get_persona_info(self, persona_id: str) -> Dict[str, Any]:
        """Get information about a persona."""
        for persona in self.personas:
            if persona['id'] == persona_id:
                return persona
        return {}
    
    def generate_response(self, user_input: str, max_length: int = 200) -> str:
        """Generate a response from the current model."""
        if self.model is None or self.tokenizer is None:
            return "❌ Model not loaded"
        
        # Format input
        prompt = f"User: {user_input}\nAssistant:"
        
        # Tokenize
        inputs = self.tokenizer(prompt, return_tensors="pt", truncation=True, max_length=512)
        if self.device == "cuda":
            inputs = {k: v.to(self.device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = self.model.generate(
                **inputs,
                max_new_tokens=max_length,
                temperature=0.7,
                do_sample=True,
                pad_token_id=self.tokenizer.eos_token_id,
                eos_token_id=self.tokenizer.eos_token_id,
            )
        
        # Decode response
        response = self.tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract just the assistant's response
        if "Assistant:" in response:
            response = response.split("Assistant:")[-1].strip()
        
        return response
    
    def list_available_personas(self) -> List[str]:
        """List all available trained personas."""
        adapters_dir = Path("artifacts/llm_adapters")
        if not adapters_dir.exists():
            return []
        
        available = []
        for persona_dir in adapters_dir.iterdir():
            if persona_dir.is_dir() and (persona_dir / "adapter_model.safetensors").exists():
                available.append(persona_dir.name)
        
        return sorted(available)
    
    def interactive_chat(self, persona_id: str):
        """Start interactive chat with a persona."""
        persona_info = self.get_persona_info(persona_id)
        if not persona_info:
            print(f"❌ Persona {persona_id} not found in configuration")
            return
        
        print(f"\n🎭 Chatting with: {persona_info.get('label', persona_id)}")
        print(f"📝 Description: {persona_info.get('blurb', 'No description available')}")
        print(f"🏷️  Tags: {', '.join(persona_info.get('psychographic_tags', []))}")
        print("\n" + "="*60)
        print("💬 Start chatting! Type 'quit' to exit, 'help' for commands")
        print("="*60)
        
        # Load the persona adapter
        if not self.load_persona_adapter(persona_id):
            return
        
        while True:
            try:
                user_input = input("\n👤 You: ").strip()
                
                if user_input.lower() in ['quit', 'exit', 'q']:
                    print("👋 Goodbye!")
                    break
                elif user_input.lower() == 'help':
                    print("\n📋 Available commands:")
                    print("  • quit/exit/q - Exit the chat")
                    print("  • help - Show this help")
                    print("  • info - Show persona information")
                    print("  • Any other text - Chat with the persona")
                    continue
                elif user_input.lower() == 'info':
                    print(f"\n📊 Persona Information:")
                    print(f"  • ID: {persona_info['id']}")
                    print(f"  • Label: {persona_info.get('label', 'N/A')}")
                    print(f"  • Description: {persona_info.get('blurb', 'N/A')}")
                    print(f"  • System Prompt: {persona_info.get('system_prompt', 'N/A')}")
                    print(f"  • Decision Constraints: {persona_info.get('decision_constraints', 'N/A')}")
                    continue
                elif not user_input:
                    continue
                
                # Generate response
                print("🤖 Assistant: ", end="", flush=True)
                response = self.generate_response(user_input)
                print(response)
                
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")

def main():
    parser = argparse.ArgumentParser(description="Test persona interaction")
    parser.add_argument("--persona", type=str, help="Specific persona to test")
    parser.add_argument("--list", action="store_true", help="List available personas")
    parser.add_argument("--base-model", type=str, default="mistralai/Mistral-7B-Instruct-v0.2",
                       help="Base model to use")
    
    args = parser.parse_args()
    
    print("🎭 Persona Interaction Tester")
    print("="*50)
    
    tester = PersonaTester(base_model=args.base_model)
    
    if args.list:
        print("\n📋 Available trained personas:")
        available = tester.list_available_personas()
        if available:
            for persona_id in available:
                persona_info = tester.get_persona_info(persona_id)
                label = persona_info.get('label', persona_id)
                print(f"  • {persona_id}: {label}")
        else:
            print("  No trained personas found in artifacts/llm_adapters/")
        return
    
    # Load base model
    tester._load_model_and_tokenizer()
    
    if args.persona:
        # Test specific persona
        if args.persona in tester.list_available_personas():
            tester.interactive_chat(args.persona)
        else:
            print(f"❌ Persona {args.persona} not found or not trained")
            print("Available personas:", tester.list_available_personas())
    else:
        # Interactive persona selection
        available = tester.list_available_personas()
        if not available:
            print("❌ No trained personas found. Please train personas first.")
            return
        
        print("\n📋 Available personas:")
        for i, persona_id in enumerate(available, 1):
            persona_info = tester.get_persona_info(persona_id)
            label = persona_info.get('label', persona_id)
            print(f"  {i}. {persona_id}: {label}")
        
        try:
            choice = input(f"\nSelect persona (1-{len(available)}): ").strip()
            choice_idx = int(choice) - 1
            
            if 0 <= choice_idx < len(available):
                selected_persona = available[choice_idx]
                tester.interactive_chat(selected_persona)
            else:
                print("❌ Invalid selection")
        except (ValueError, KeyboardInterrupt):
            print("👋 Goodbye!")

if __name__ == "__main__":
    main()
