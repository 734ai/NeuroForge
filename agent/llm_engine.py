#!/usr/bin/env python3
"""
NeuroForge LLM Integration Engine
Author: Muzan Sano

This module provides the core LLM integration framework for NeuroForge,
enabling AI-powered code analysis, generation, and automation.
"""

import asyncio
import json
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, AsyncGenerator
import logging

try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    ANTHROPIC_AVAILABLE = False

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class LLMProvider(Enum):
    """Available LLM providers"""
    OPENAI = "openai"
    ANTHROPIC = "anthropic"
    LOCAL = "local"
    MOCK = "mock"


class LLMCapability(Enum):
    """LLM capabilities for different tasks"""
    CODE_ANALYSIS = "code_analysis"
    CODE_GENERATION = "code_generation"
    CODE_REFACTORING = "code_refactoring"
    DOCUMENTATION = "documentation"
    DEBUGGING = "debugging"
    TESTING = "testing"
    ARCHITECTURE = "architecture"
    SECURITY = "security"


@dataclass
class LLMConfig:
    """Configuration for LLM integration"""
    provider: LLMProvider
    model: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    max_tokens: int = 4096
    temperature: float = 0.1
    timeout: int = 30
    rate_limit: int = 10  # requests per minute
    capabilities: List[LLMCapability] = None
    
    def __post_init__(self):
        if self.capabilities is None:
            self.capabilities = list(LLMCapability)


@dataclass
class LLMRequest:
    """LLM request structure"""
    prompt: str
    capability: LLMCapability
    context: Dict[str, Any] = None
    code_context: Optional[str] = None
    workspace_path: Optional[str] = None
    max_tokens: Optional[int] = None
    temperature: Optional[float] = None
    
    def __post_init__(self):
        if self.context is None:
            self.context = {}


@dataclass
class LLMResponse:
    """LLM response structure"""
    content: str
    capability: LLMCapability
    tokens_used: int
    response_time: float
    confidence: float = 0.0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


class LLMProvider_Interface(ABC):
    """Abstract base class for LLM providers"""
    
    def __init__(self, config: LLMConfig):
        self.config = config
        self.request_count = 0
        self.last_request_time = 0
    
    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM"""
        pass
    
    async def check_rate_limit(self) -> bool:
        """Check if we're within rate limits"""
        current_time = time.time()
        if current_time - self.last_request_time < 60:  # Within last minute
            if self.request_count >= self.config.rate_limit:
                return False
        else:
            self.request_count = 0  # Reset counter after a minute
        return True
    
    def update_request_counter(self):
        """Update request tracking"""
        current_time = time.time()
        if current_time - self.last_request_time >= 60:
            self.request_count = 0
        self.request_count += 1
        self.last_request_time = current_time


class OpenAIProvider(LLMProvider_Interface):
    """OpenAI LLM provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not OPENAI_AVAILABLE:
            raise ImportError("OpenAI library not available. Install with: pip install openai")
        
        self.client = openai.AsyncOpenAI(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI"""
        if not await self.check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        start_time = time.time()
        
        # Build system prompt based on capability
        system_prompt = self._build_system_prompt(request.capability)
        
        # Build user prompt with context
        user_prompt = self._build_user_prompt(request)
        
        try:
            response = await self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature,
                timeout=self.config.timeout
            )
            
            self.update_request_counter()
            
            return LLMResponse(
                content=response.choices[0].message.content,
                capability=request.capability,
                tokens_used=response.usage.total_tokens,
                response_time=time.time() - start_time,
                confidence=0.8,  # Default confidence for OpenAI
                metadata={
                    "model": self.config.model,
                    "finish_reason": response.choices[0].finish_reason
                }
            )
            
        except Exception as e:
            logger.error(f"OpenAI request failed: {e}")
            raise
    
    def _build_system_prompt(self, capability: LLMCapability) -> str:
        """Build system prompt based on capability"""
        prompts = {
            LLMCapability.CODE_ANALYSIS: """You are an expert code analyst. Analyze the provided code for:
- Structure and design patterns
- Potential bugs and issues
- Performance optimizations
- Best practices compliance
- Security vulnerabilities
Provide detailed, actionable insights.""",
            
            LLMCapability.CODE_GENERATION: """You are an expert software developer. Generate high-quality code that:
- Follows best practices and conventions
- Is well-documented and readable
- Includes error handling
- Is performant and efficient
- Follows the specified requirements exactly""",
            
            LLMCapability.CODE_REFACTORING: """You are an expert code refactoring specialist. When refactoring code:
- Maintain existing functionality
- Improve readability and maintainability
- Optimize performance where possible
- Follow modern best practices
- Provide clear explanations of changes""",
            
            LLMCapability.DOCUMENTATION: """You are a technical documentation expert. Create comprehensive documentation that:
- Is clear and easy to understand
- Includes examples and use cases
- Follows standard documentation formats
- Is accurate and up-to-date
- Helps developers understand and use the code""",
            
            LLMCapability.DEBUGGING: """You are an expert debugger. Help identify and fix issues by:
- Analyzing error messages and stack traces
- Identifying root causes
- Suggesting specific fixes
- Providing debugging strategies
- Explaining the underlying problems""",
            
            LLMCapability.TESTING: """You are a testing expert. Create comprehensive tests that:
- Cover all functionality and edge cases
- Follow testing best practices
- Are maintainable and readable
- Include both unit and integration tests
- Help ensure code quality and reliability""",
            
            LLMCapability.ARCHITECTURE: """You are a software architecture expert. Provide architectural guidance that:
- Considers scalability and maintainability
- Follows established patterns and principles
- Balances complexity and simplicity
- Addresses non-functional requirements
- Provides clear design decisions""",
            
            LLMCapability.SECURITY: """You are a security expert. Analyze code for security issues including:
- Input validation and sanitization
- Authentication and authorization
- Data encryption and protection
- Common vulnerabilities (OWASP Top 10)
- Security best practices"""
        }
        
        return prompts.get(capability, "You are a helpful AI assistant for software development.")
    
    def _build_user_prompt(self, request: LLMRequest) -> str:
        """Build user prompt with context"""
        prompt_parts = [request.prompt]
        
        if request.code_context:
            prompt_parts.append(f"\n\nCode Context:\n```\n{request.code_context}\n```")
        
        if request.context:
            context_str = json.dumps(request.context, indent=2)
            prompt_parts.append(f"\n\nAdditional Context:\n{context_str}")
        
        return "\n".join(prompt_parts)


class AnthropicProvider(LLMProvider_Interface):
    """Anthropic Claude LLM provider"""
    
    def __init__(self, config: LLMConfig):
        super().__init__(config)
        if not ANTHROPIC_AVAILABLE:
            raise ImportError("Anthropic library not available. Install with: pip install anthropic")
        
        self.client = anthropic.AsyncAnthropic(
            api_key=config.api_key,
            base_url=config.base_url
        )
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic Claude"""
        if not await self.check_rate_limit():
            raise Exception("Rate limit exceeded")
        
        start_time = time.time()
        
        # Build prompt with context
        full_prompt = self._build_full_prompt(request)
        
        try:
            response = await self.client.messages.create(
                model=self.config.model,
                max_tokens=request.max_tokens or self.config.max_tokens,
                temperature=request.temperature or self.config.temperature,
                messages=[{"role": "user", "content": full_prompt}]
            )
            
            self.update_request_counter()
            
            return LLMResponse(
                content=response.content[0].text,
                capability=request.capability,
                tokens_used=response.usage.input_tokens + response.usage.output_tokens,
                response_time=time.time() - start_time,
                confidence=0.85,  # Default confidence for Claude
                metadata={
                    "model": self.config.model,
                    "stop_reason": response.stop_reason
                }
            )
            
        except Exception as e:
            logger.error(f"Anthropic request failed: {e}")
            raise
    
    def _build_full_prompt(self, request: LLMRequest) -> str:
        """Build full prompt for Anthropic"""
        # Similar to OpenAI but in single prompt format
        system_prompt = self._build_system_prompt(request.capability)
        user_prompt = self._build_user_prompt(request)
        
        return f"{system_prompt}\n\n{user_prompt}"
    
    def _build_system_prompt(self, capability: LLMCapability) -> str:
        """Build system prompt based on capability (same as OpenAI)"""
        return OpenAIProvider._build_system_prompt(self, capability)
    
    def _build_user_prompt(self, request: LLMRequest) -> str:
        """Build user prompt with context (same as OpenAI)"""
        return OpenAIProvider._build_user_prompt(self, request)


class MockProvider(LLMProvider_Interface):
    """Mock LLM provider for testing and development"""
    
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate mock response"""
        await asyncio.sleep(0.1)  # Simulate network delay
        
        mock_responses = {
            LLMCapability.CODE_ANALYSIS: "Mock code analysis: The code looks good with minor improvements needed.",
            LLMCapability.CODE_GENERATION: f"# Mock generated code for: {request.prompt}\ndef mock_function():\n    return 'Generated code'",
            LLMCapability.CODE_REFACTORING: "Mock refactoring suggestions: Extract method, improve naming.",
            LLMCapability.DOCUMENTATION: f"# Mock Documentation\n\n{request.prompt}\n\nThis is mock documentation.",
            LLMCapability.DEBUGGING: "Mock debugging: Check line 42 for potential null pointer exception.",
            LLMCapability.TESTING: "Mock test generation: def test_mock(): assert True",
            LLMCapability.ARCHITECTURE: "Mock architecture: Consider using microservices pattern.",
            LLMCapability.SECURITY: "Mock security analysis: No major security issues found."
        }
        
        content = mock_responses.get(request.capability, f"Mock response for {request.capability.value}")
        
        return LLMResponse(
            content=content,
            capability=request.capability,
            tokens_used=100,
            response_time=0.1,
            confidence=1.0,
            metadata={"provider": "mock"}
        )


class LLMEngine:
    """Main LLM engine orchestrating all providers and capabilities"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.providers: Dict[LLMProvider, LLMProvider_Interface] = {}
        self.default_provider = None
        self.request_history: List[Dict[str, Any]] = []
        
        print("NeuroForge LLM Engine initialized")
    
    def register_provider(self, config: LLMConfig, is_default: bool = False) -> None:
        """Register an LLM provider"""
        try:
            if config.provider == LLMProvider.OPENAI:
                provider = OpenAIProvider(config)
            elif config.provider == LLMProvider.ANTHROPIC:
                provider = AnthropicProvider(config)
            elif config.provider == LLMProvider.MOCK:
                provider = MockProvider(config)
            else:
                raise ValueError(f"Unsupported provider: {config.provider}")
            
            self.providers[config.provider] = provider
            
            if is_default or not self.default_provider:
                self.default_provider = config.provider
                
            print(f"Registered LLM provider: {config.provider.value} with model {config.model}")
            
        except Exception as e:
            logger.error(f"Failed to register provider {config.provider.value}: {e}")
            raise
    
    async def generate_response(self, request: LLMRequest, 
                              provider: Optional[LLMProvider] = None) -> LLMResponse:
        """Generate response using specified or default provider"""
        provider = provider or self.default_provider
        
        if provider not in self.providers:
            raise ValueError(f"Provider {provider} not registered")
        
        # Add workspace context if not provided
        if not request.workspace_path:
            request.workspace_path = str(self.workspace_root)
        
        start_time = time.time()
        
        try:
            response = await self.providers[provider].generate_response(request)
            
            # Log request/response for analysis
            self.request_history.append({
                "timestamp": start_time,
                "provider": provider.value,
                "capability": request.capability.value,
                "prompt_length": len(request.prompt),
                "response_length": len(response.content),
                "tokens_used": response.tokens_used,
                "response_time": response.response_time,
                "confidence": response.confidence
            })
            
            return response
            
        except Exception as e:
            logger.error(f"LLM request failed: {e}")
            raise
    
    async def analyze_code(self, code: str, context: Dict[str, Any] = None) -> LLMResponse:
        """Analyze code for issues and improvements"""
        request = LLMRequest(
            prompt="Analyze this code for potential issues, improvements, and best practices:",
            capability=LLMCapability.CODE_ANALYSIS,
            code_context=code,
            context=context or {}
        )
        return await self.generate_response(request)
    
    async def generate_code(self, prompt: str, context: Dict[str, Any] = None) -> LLMResponse:
        """Generate code based on requirements"""
        request = LLMRequest(
            prompt=prompt,
            capability=LLMCapability.CODE_GENERATION,
            context=context or {}
        )
        return await self.generate_response(request)
    
    async def refactor_code(self, code: str, instructions: str, 
                           context: Dict[str, Any] = None) -> LLMResponse:
        """Refactor code according to instructions"""
        request = LLMRequest(
            prompt=f"Refactor this code according to these instructions: {instructions}",
            capability=LLMCapability.CODE_REFACTORING,
            code_context=code,
            context=context or {}
        )
        return await self.generate_response(request)
    
    async def generate_documentation(self, code: str, doc_type: str = "general",
                                   context: Dict[str, Any] = None) -> LLMResponse:
        """Generate documentation for code"""
        request = LLMRequest(
            prompt=f"Generate {doc_type} documentation for this code:",
            capability=LLMCapability.DOCUMENTATION,
            code_context=code,
            context=context or {}
        )
        return await self.generate_response(request)
    
    async def debug_issue(self, error_message: str, code: str = None,
                         context: Dict[str, Any] = None) -> LLMResponse:
        """Debug code issues and provide solutions"""
        request = LLMRequest(
            prompt=f"Help debug this error: {error_message}",
            capability=LLMCapability.DEBUGGING,
            code_context=code,
            context=context or {}
        )
        return await self.generate_response(request)
    
    async def generate_tests(self, code: str, test_type: str = "unit",
                            context: Dict[str, Any] = None) -> LLMResponse:
        """Generate tests for code"""
        request = LLMRequest(
            prompt=f"Generate {test_type} tests for this code:",
            capability=LLMCapability.TESTING,
            code_context=code,
            context=context or {}
        )
        return await self.generate_response(request)
    
    def get_available_providers(self) -> List[LLMProvider]:
        """Get list of registered providers"""
        return list(self.providers.keys())
    
    def get_provider_capabilities(self, provider: LLMProvider) -> List[LLMCapability]:
        """Get capabilities of a specific provider"""
        if provider in self.providers:
            return self.providers[provider].config.capabilities
        return []
    
    def get_request_stats(self) -> Dict[str, Any]:
        """Get statistics about LLM usage"""
        if not self.request_history:
            return {"total_requests": 0}
        
        total_requests = len(self.request_history)
        total_tokens = sum(req["tokens_used"] for req in self.request_history)
        avg_response_time = sum(req["response_time"] for req in self.request_history) / total_requests
        avg_confidence = sum(req["confidence"] for req in self.request_history) / total_requests
        
        capabilities_used = {}
        for req in self.request_history:
            cap = req["capability"]
            capabilities_used[cap] = capabilities_used.get(cap, 0) + 1
        
        return {
            "total_requests": total_requests,
            "total_tokens": total_tokens,
            "average_response_time": avg_response_time,
            "average_confidence": avg_confidence,
            "capabilities_used": capabilities_used,
            "providers_used": list(set(req["provider"] for req in self.request_history))
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_llm_engine():
        """Test the LLM engine with mock provider"""
        engine = LLMEngine()
        
        # Register mock provider for testing
        mock_config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock-model"
        )
        engine.register_provider(mock_config, is_default=True)
        
        # Test code analysis
        test_code = """
def calculate_sum(a, b):
    result = a + b
    return result
"""
        
        print("Testing code analysis...")
        analysis = await engine.analyze_code(test_code)
        print(f"Analysis: {analysis.content}")
        
        print("\nTesting code generation...")
        generation = await engine.generate_code("Create a function to calculate factorial")
        print(f"Generated: {generation.content}")
        
        print("\nTesting documentation generation...")
        docs = await engine.generate_documentation(test_code)
        print(f"Documentation: {docs.content}")
        
        print("\nLLM Engine Statistics:")
        stats = engine.get_request_stats()
        for key, value in stats.items():
            print(f"  {key}: {value}")
        
        print("\n✅ LLM Engine test completed!")
    
    # Run test
    asyncio.run(test_llm_engine())
