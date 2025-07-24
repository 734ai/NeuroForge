#!/usr/bin/env python3
"""
NeuroForge LLM Refactoring Assistant Plugin
Author: Muzan Sano

This plugin uses LLM capabilities to automatically suggest and apply code refactoring
improvements, including performance optimization, code simplification, and modernization.
"""

import asyncio
import json
import re
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

# Import LLM engine
from agent.llm_engine import LLMEngine, LLMConfig, LLMProvider, LLMCapability, LLMRequest


class RefactoringType(Enum):
    """Types of refactoring operations"""
    EXTRACT_METHOD = "extract_method"
    EXTRACT_CLASS = "extract_class"
    RENAME_VARIABLE = "rename_variable"
    SIMPLIFY_LOGIC = "simplify_logic"
    OPTIMIZE_PERFORMANCE = "optimize_performance"
    MODERNIZE_SYNTAX = "modernize_syntax"
    IMPROVE_READABILITY = "improve_readability"
    REDUCE_COMPLEXITY = "reduce_complexity"
    ELIMINATE_DUPLICATION = "eliminate_duplication"
    IMPROVE_ERROR_HANDLING = "improve_error_handling"


class RefactoringImpact(Enum):
    """Impact level of refactoring changes"""
    MINIMAL = "minimal"        # Simple renaming, formatting
    MODERATE = "moderate"      # Logic simplification
    SIGNIFICANT = "significant" # Structure changes
    MAJOR = "major"           # Architecture changes


@dataclass
class RefactoringStep:
    """A single refactoring step"""
    step_id: str
    description: str
    original_code: str
    refactored_code: str
    explanation: str
    impact: RefactoringImpact
    confidence: float
    file_path: Optional[str] = None
    line_start: Optional[int] = None
    line_end: Optional[int] = None


@dataclass
class RefactoringPlan:
    """A complete refactoring plan"""
    plan_id: str
    target_files: List[str]
    refactoring_types: List[RefactoringType]
    steps: List[RefactoringStep]
    estimated_impact: RefactoringImpact
    benefits: List[str]
    risks: List[str]
    prerequisites: List[str]
    execution_order: List[str]  # Step IDs in execution order


@dataclass
class RefactoringResult:
    """Result of executing a refactoring plan"""
    plan_id: str
    executed_steps: List[str]
    failed_steps: List[str]
    files_modified: List[str]
    execution_time: float
    success_rate: float
    final_validation: bool
    error_messages: List[str]


class LLMRefactoringAssistant:
    """LLM-powered refactoring assistant"""
    
    def __init__(self, workspace_root: str = "."):
        self.workspace_root = Path(workspace_root)
        self.llm_engine = LLMEngine(workspace_root)
        self.refactoring_history: List[RefactoringPlan] = []
        
        # Initialize with mock provider by default
        self._setup_default_provider()
        
        print("LLM Refactoring Assistant initialized")
    
    def _setup_default_provider(self):
        """Setup default LLM provider (similar to code analyzer)"""
        import os
        
        # Try OpenAI first
        openai_key = os.getenv("OPENAI_API_KEY")
        if openai_key:
            try:
                config = LLMConfig(
                    provider=LLMProvider.OPENAI,
                    model="gpt-4-turbo-preview",
                    api_key=openai_key,
                    max_tokens=4096,
                    temperature=0.1
                )
                self.llm_engine.register_provider(config, is_default=True)
                print("Using OpenAI GPT-4 for refactoring")
                return
            except Exception as e:
                print(f"Failed to setup OpenAI: {e}")
        
        # Fallback to mock
        config = LLMConfig(
            provider=LLMProvider.MOCK,
            model="mock-refactorer"
        )
        self.llm_engine.register_provider(config, is_default=True)
        print("Using mock provider for refactoring")
    
    async def analyze_refactoring_opportunities(self, file_path: str) -> List[Dict[str, Any]]:
        """Analyze code for refactoring opportunities"""
        file_path = Path(file_path)
        
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        prompt = """Analyze this code for refactoring opportunities. For each opportunity, provide:
1. Type of refactoring (extract method, simplify logic, etc.)
2. Location (line numbers if possible)
3. Description of the improvement
4. Expected benefits
5. Risk level (low/medium/high)

Focus on:
- Long methods that should be broken down
- Duplicated code
- Complex conditional logic
- Performance improvements
- Readability improvements
- Modern syntax opportunities

Format your response as a structured list."""
        
        request = LLMRequest(
            prompt=prompt,
            capability=LLMCapability.CODE_REFACTORING,
            code_context=code_content,
            context={
                "file_path": str(file_path),
                "analysis_type": "refactoring_opportunities"
            }
        )
        
        response = await self.llm_engine.generate_response(request)
        
        # Parse opportunities from response
        return self._parse_refactoring_opportunities(response.content, str(file_path))
    
    async def create_refactoring_plan(self, file_paths: List[str], 
                                    refactoring_types: List[RefactoringType] = None) -> RefactoringPlan:
        """Create a comprehensive refactoring plan"""
        if refactoring_types is None:
            refactoring_types = [RefactoringType.IMPROVE_READABILITY, RefactoringType.SIMPLIFY_LOGIC]
        
        plan_id = f"refactor_{len(self.refactoring_history)}"
        all_steps = []
        
        print(f"Creating refactoring plan for {len(file_paths)} files...")
        
        for file_path in file_paths:
            file_steps = await self._analyze_file_for_refactoring(file_path, refactoring_types)
            all_steps.extend(file_steps)
        
        # Determine execution order
        execution_order = self._determine_execution_order(all_steps)
        
        # Assess overall impact
        estimated_impact = self._assess_overall_impact(all_steps)
        
        # Generate benefits and risks
        benefits, risks = await self._generate_benefits_and_risks(all_steps)
        
        plan = RefactoringPlan(
            plan_id=plan_id,
            target_files=file_paths,
            refactoring_types=refactoring_types,
            steps=all_steps,
            estimated_impact=estimated_impact,
            benefits=benefits,
            risks=risks,
            prerequisites=["Backup files", "Run tests before refactoring", "Review changes carefully"],
            execution_order=execution_order
        )
        
        self.refactoring_history.append(plan)
        print(f"Created refactoring plan with {len(all_steps)} steps")
        
        return plan
    
    async def _analyze_file_for_refactoring(self, file_path: str, 
                                          refactoring_types: List[RefactoringType]) -> List[RefactoringStep]:
        """Analyze a single file for specific refactoring types"""
        file_path = Path(file_path)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            code_content = f.read()
        
        steps = []
        
        for refactoring_type in refactoring_types:
            prompt = self._get_refactoring_prompt(refactoring_type)
            
            request = LLMRequest(
                prompt=prompt,
                capability=LLMCapability.CODE_REFACTORING,
                code_context=code_content,
                context={
                    "file_path": str(file_path),
                    "refactoring_type": refactoring_type.value
                }
            )
            
            response = await self.llm_engine.generate_response(request)
            
            # Parse refactoring steps from response
            type_steps = self._parse_refactoring_steps(response.content, str(file_path), refactoring_type)
            steps.extend(type_steps)
        
        return steps
    
    def _get_refactoring_prompt(self, refactoring_type: RefactoringType) -> str:
        """Get specific prompt for refactoring type"""
        prompts = {
            RefactoringType.EXTRACT_METHOD: """
            Identify long methods (>20 lines) that should be broken down. For each:
            1. Show the original method
            2. Propose how to extract smaller methods
            3. Provide the refactored code
            4. Explain the benefits
            """,
            
            RefactoringType.SIMPLIFY_LOGIC: """
            Find complex conditional logic that can be simplified. Look for:
            - Nested if statements
            - Complex boolean expressions
            - Switch statements that can be refactored
            Provide simplified alternatives.
            """,
            
            RefactoringType.OPTIMIZE_PERFORMANCE: """
            Identify performance optimization opportunities:
            - Inefficient loops
            - Unnecessary computations
            - Memory usage improvements
            - Algorithm optimizations
            Provide optimized code versions.
            """,
            
            RefactoringType.MODERNIZE_SYNTAX: """
            Update code to use modern language features:
            - Replace old patterns with modern equivalents
            - Use newer syntax features
            - Improve type annotations
            Show before and after code.
            """,
            
            RefactoringType.IMPROVE_READABILITY: """
            Improve code readability by:
            - Better variable/function names
            - Clearer structure
            - Better comments
            - Consistent formatting
            Show improved versions.
            """,
            
            RefactoringType.REDUCE_COMPLEXITY: """
            Reduce code complexity by:
            - Breaking down complex functions
            - Reducing cyclomatic complexity
            - Simplifying control flow
            - Removing unnecessary complexity
            """,
            
            RefactoringType.ELIMINATE_DUPLICATION: """
            Find and eliminate code duplication:
            - Identify duplicated blocks
            - Suggest common functions/methods
            - Show how to refactor duplicated code
            - Provide DRY alternatives
            """
        }
        
        return prompts.get(refactoring_type, "Analyze this code for refactoring opportunities.")
    
    def _parse_refactoring_opportunities(self, response_content: str, file_path: str) -> List[Dict[str, Any]]:
        """Parse refactoring opportunities from LLM response"""
        opportunities = []
        
        # Simple parsing - in production you'd want more sophisticated parsing
        lines = response_content.split('\n')
        current_opportunity = {}
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Look for opportunity markers
            if 'opportunity' in line.lower() or 'refactoring' in line.lower():
                if current_opportunity:
                    opportunities.append(current_opportunity)
                current_opportunity = {
                    "description": line,
                    "file_path": file_path,
                    "type": "general",
                    "benefits": [],
                    "risk": "medium"
                }
            elif current_opportunity:
                # Add details to current opportunity
                if 'benefit' in line.lower():
                    current_opportunity['benefits'].append(line)
                elif 'risk' in line.lower():
                    current_opportunity['risk'] = self._extract_risk_level(line)
                elif 'type' in line.lower():
                    current_opportunity['type'] = self._extract_refactoring_type(line)
        
        if current_opportunity:
            opportunities.append(current_opportunity)
        
        return opportunities
    
    def _parse_refactoring_steps(self, response_content: str, file_path: str, 
                                refactoring_type: RefactoringType) -> List[RefactoringStep]:
        """Parse refactoring steps from LLM response"""
        steps = []
        
        # Look for code blocks in the response
        code_blocks = re.findall(r'```[\w]*\n(.*?)\n```', response_content, re.DOTALL)
        
        if len(code_blocks) >= 2:  # Original and refactored code
            step = RefactoringStep(
                step_id=f"{refactoring_type.value}_{len(steps)}",
                description=f"{refactoring_type.value.replace('_', ' ').title()} refactoring",
                original_code=code_blocks[0] if len(code_blocks) > 0 else "",
                refactored_code=code_blocks[1] if len(code_blocks) > 1 else "",
                explanation=response_content,
                impact=RefactoringImpact.MODERATE,
                confidence=0.8,
                file_path=file_path
            )
            steps.append(step)
        else:
            # Create a general step if no code blocks found
            step = RefactoringStep(
                step_id=f"{refactoring_type.value}_general",
                description=f"General {refactoring_type.value.replace('_', ' ')} improvements",
                original_code="",
                refactored_code="",
                explanation=response_content,
                impact=RefactoringImpact.MINIMAL,
                confidence=0.5,
                file_path=file_path
            )
            steps.append(step)
        
        return steps
    
    def _determine_execution_order(self, steps: List[RefactoringStep]) -> List[str]:
        """Determine optimal execution order for refactoring steps"""
        # Sort by impact level (minimal first, then moderate, etc.)
        impact_order = {
            RefactoringImpact.MINIMAL: 1,
            RefactoringImpact.MODERATE: 2,
            RefactoringImpact.SIGNIFICANT: 3,
            RefactoringImpact.MAJOR: 4
        }
        
        sorted_steps = sorted(steps, key=lambda s: impact_order.get(s.impact, 999))
        return [step.step_id for step in sorted_steps]
    
    def _assess_overall_impact(self, steps: List[RefactoringStep]) -> RefactoringImpact:
        """Assess overall impact of all refactoring steps"""
        if not steps:
            return RefactoringImpact.MINIMAL
        
        impact_scores = {
            RefactoringImpact.MINIMAL: 1,
            RefactoringImpact.MODERATE: 2,
            RefactoringImpact.SIGNIFICANT: 3,
            RefactoringImpact.MAJOR: 4
        }
        
        max_impact = max(impact_scores.get(step.impact, 1) for step in steps)
        
        for impact, score in impact_scores.items():
            if score == max_impact:
                return impact
        
        return RefactoringImpact.MODERATE
    
    async def _generate_benefits_and_risks(self, steps: List[RefactoringStep]) -> Tuple[List[str], List[str]]:
        """Generate benefits and risks for the refactoring plan"""
        if not steps:
            return [], []
        
        steps_summary = "\n".join([
            f"- {step.description}: {step.impact.value} impact"
            for step in steps[:10]  # Limit for token efficiency
        ])
        
        prompt = f"""Based on these refactoring steps, list:
1. The main benefits of this refactoring plan
2. The potential risks and things to watch out for

Refactoring steps:
{steps_summary}

Provide specific, actionable insights."""
        
        request = LLMRequest(
            prompt=prompt,
            capability=LLMCapability.CODE_REFACTORING,
            context={"analysis_type": "benefits_risks", "steps_count": len(steps)}
        )
        
        response = await self.llm_engine.generate_response(request)
        
        # Parse benefits and risks
        content = response.content.lower()
        
        if 'benefits' in content and 'risks' in content:
            parts = content.split('risks')
            benefits_text = parts[0].replace('benefits', '').strip()
            risks_text = parts[1].strip()
        else:
            benefits_text = content[:len(content)//2]
            risks_text = content[len(content)//2:]
        
        benefits = [b.strip() for b in benefits_text.split('\n') if b.strip() and len(b.strip()) > 10][:5]
        risks = [r.strip() for r in risks_text.split('\n') if r.strip() and len(r.strip()) > 10][:5]
        
        # Default fallbacks
        if not benefits:
            benefits = [
                "Improved code readability and maintainability",
                "Better performance and efficiency",
                "Reduced technical debt",
                "Enhanced code quality and structure"
            ]
        
        if not risks:
            risks = [
                "Potential introduction of bugs during refactoring",
                "Breaking existing functionality if not tested properly",
                "Time investment required for implementation",
                "Need for thorough testing after changes"
            ]
        
        return benefits, risks
    
    async def execute_refactoring_plan(self, plan: RefactoringPlan, 
                                     dry_run: bool = True) -> RefactoringResult:
        """Execute a refactoring plan"""
        print(f"Executing refactoring plan {plan.plan_id} (dry_run={dry_run})...")
        
        start_time = asyncio.get_event_loop().time()
        executed_steps = []
        failed_steps = []
        files_modified = []
        error_messages = []
        
        for step_id in plan.execution_order:
            step = next((s for s in plan.steps if s.step_id == step_id), None)
            if not step:
                continue
            
            try:
                print(f"Executing step: {step.description}")
                
                if not dry_run and step.refactored_code and step.file_path:
                    # Apply the refactoring
                    success = await self._apply_refactoring_step(step)
                    if success:
                        executed_steps.append(step_id)
                        if step.file_path not in files_modified:
                            files_modified.append(step.file_path)
                    else:
                        failed_steps.append(step_id)
                        error_messages.append(f"Failed to apply step {step_id}")
                else:
                    # Dry run - just log
                    print(f"  [DRY RUN] Would apply: {step.description}")
                    executed_steps.append(step_id)
                
            except Exception as e:
                failed_steps.append(step_id)
                error_messages.append(f"Error in step {step_id}: {str(e)}")
        
        execution_time = asyncio.get_event_loop().time() - start_time
        success_rate = len(executed_steps) / len(plan.steps) if plan.steps else 0
        
        result = RefactoringResult(
            plan_id=plan.plan_id,
            executed_steps=executed_steps,
            failed_steps=failed_steps,
            files_modified=files_modified,
            execution_time=execution_time,
            success_rate=success_rate,
            final_validation=len(failed_steps) == 0,
            error_messages=error_messages
        )
        
        print(f"Refactoring completed: {len(executed_steps)}/{len(plan.steps)} steps successful")
        
        return result
    
    async def _apply_refactoring_step(self, step: RefactoringStep) -> bool:
        """Apply a single refactoring step to the file"""
        try:
            if not step.file_path or not step.refactored_code:
                return False
            
            file_path = Path(step.file_path)
            
            # Read current file content
            with open(file_path, 'r', encoding='utf-8') as f:
                current_content = f.read()
            
            # For now, we'll use simple string replacement
            # In production, you'd want more sophisticated AST-based refactoring
            if step.original_code:
                new_content = current_content.replace(step.original_code, step.refactored_code)
            else:
                # If no original code specified, append the refactored code
                new_content = current_content + "\n\n" + step.refactored_code
            
            # Write back to file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            
            return True
            
        except Exception as e:
            print(f"Error applying refactoring step: {e}")
            return False
    
    def _extract_risk_level(self, text: str) -> str:
        """Extract risk level from text"""
        text_lower = text.lower()
        if any(word in text_lower for word in ['low', 'minimal', 'safe']):
            return "low"
        elif any(word in text_lower for word in ['high', 'dangerous', 'risky']):
            return "high"
        else:
            return "medium"
    
    def _extract_refactoring_type(self, text: str) -> str:
        """Extract refactoring type from text"""
        text_lower = text.lower()
        for refactoring_type in RefactoringType:
            if refactoring_type.value.replace('_', ' ') in text_lower:
                return refactoring_type.value
        return "general"
    
    def export_plan(self, plan: RefactoringPlan, format: str = "json") -> str:
        """Export refactoring plan to different formats"""
        if format == "json":
            return json.dumps({
                "plan_id": plan.plan_id,
                "target_files": plan.target_files,
                "refactoring_types": [rt.value for rt in plan.refactoring_types],
                "steps": [
                    {
                        "step_id": s.step_id,
                        "description": s.description,
                        "impact": s.impact.value,
                        "confidence": s.confidence,
                        "file_path": s.file_path
                    }
                    for s in plan.steps
                ],
                "estimated_impact": plan.estimated_impact.value,
                "benefits": plan.benefits,
                "risks": plan.risks,
                "prerequisites": plan.prerequisites,
                "execution_order": plan.execution_order
            }, indent=2)
        elif format == "markdown":
            return self._export_plan_markdown(plan)
        else:
            raise ValueError(f"Unsupported format: {format}")
    
    def _export_plan_markdown(self, plan: RefactoringPlan) -> str:
        """Export plan as Markdown"""
        md = f"""# Refactoring Plan: {plan.plan_id}

## Overview
- **Target Files:** {len(plan.target_files)}
- **Total Steps:** {len(plan.steps)}
- **Estimated Impact:** {plan.estimated_impact.value.title()}

## Benefits
"""
        for benefit in plan.benefits:
            md += f"- {benefit}\n"
        
        md += "\n## Risks\n"
        for risk in plan.risks:
            md += f"- {risk}\n"
        
        md += "\n## Prerequisites\n"
        for prereq in plan.prerequisites:
            md += f"- {prereq}\n"
        
        md += "\n## Refactoring Steps\n"
        for i, step_id in enumerate(plan.execution_order, 1):
            step = next((s for s in plan.steps if s.step_id == step_id), None)
            if step:
                md += f"\n### {i}. {step.description}\n"
                md += f"**Impact:** {step.impact.value}\n"
                md += f"**Confidence:** {step.confidence:.2f}\n"
                md += f"**File:** {step.file_path}\n\n"
                if step.explanation:
                    md += f"{step.explanation}\n\n"
        
        return md


# Plugin interface for NeuroForge task agent
async def run_plugin(task_id: str, parameters: Dict[str, Any], context: Dict[str, Any]) -> Dict[str, Any]:
    """Main plugin entry point"""
    workspace_path = parameters.get('workspace_path', '.')
    file_paths = parameters.get('file_paths', [])
    refactoring_types = parameters.get('refactoring_types', ['improve_readability'])
    dry_run = parameters.get('dry_run', True)
    
    try:
        # Create refactoring assistant
        assistant = LLMRefactoringAssistant(workspace_path)
        
        # Convert string refactoring types to enums
        refactoring_enums = []
        for rt in refactoring_types:
            try:
                refactoring_enums.append(RefactoringType(rt))
            except ValueError:
                print(f"Unknown refactoring type: {rt}")
        
        if not refactoring_enums:
            refactoring_enums = [RefactoringType.IMPROVE_READABILITY]
        
        # Create refactoring plan
        plan = await assistant.create_refactoring_plan(file_paths, refactoring_enums)
        
        # Execute plan
        result = await assistant.execute_refactoring_plan(plan, dry_run)
        
        # Export plan
        plan_json = assistant.export_plan(plan, "json")
        plan_file = Path(workspace_path) / f".neuroforge/refactoring/plan_{task_id}.json"
        plan_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(plan_file, 'w') as f:
            f.write(plan_json)
        
        return {
            "status": "completed",
            "plan_id": plan.plan_id,
            "plan_file": str(plan_file),
            "total_steps": len(plan.steps),
            "executed_steps": len(result.executed_steps),
            "failed_steps": len(result.failed_steps),
            "success_rate": result.success_rate,
            "files_modified": result.files_modified,
            "dry_run": dry_run,
            "execution_time": result.execution_time,
            "estimated_impact": plan.estimated_impact.value,
            "benefits": plan.benefits[:3],  # Top 3 benefits
            "risks": plan.risks[:3]  # Top 3 risks
        }
        
    except Exception as e:
        return {
            "status": "failed",
            "error": str(e)
        }


# Example usage and testing
if __name__ == "__main__":
    async def test_refactoring_assistant():
        """Test the LLM refactoring assistant"""
        assistant = LLMRefactoringAssistant(".")
        
        # Test file analysis
        test_files = ["agent/memory_engine.py"]  # Use existing file
        
        print("Creating refactoring plan...")
        plan = await assistant.create_refactoring_plan(
            test_files, 
            [RefactoringType.IMPROVE_READABILITY, RefactoringType.SIMPLIFY_LOGIC]
        )
        
        print(f"\nRefactoring Plan Results:")
        print(f"Plan ID: {plan.plan_id}")
        print(f"Steps: {len(plan.steps)}")
        print(f"Estimated Impact: {plan.estimated_impact.value}")
        
        print(f"\nBenefits:")
        for benefit in plan.benefits[:3]:
            print(f"- {benefit}")
        
        print(f"\nRisks:")
        for risk in plan.risks[:3]:
            print(f"- {risk}")
        
        # Execute plan (dry run)
        print(f"\nExecuting plan (dry run)...")
        result = await assistant.execute_refactoring_plan(plan, dry_run=True)
        
        print(f"Execution Results:")
        print(f"Success Rate: {result.success_rate:.2f}")
        print(f"Executed Steps: {len(result.executed_steps)}")
        print(f"Failed Steps: {len(result.failed_steps)}")
        
        # Export plan
        markdown_plan = assistant.export_plan(plan, "markdown")
        print(f"\nExported plan length: {len(markdown_plan)} characters")
        
        print("\n✅ LLM Refactoring Assistant test completed!")
    
    # Run test
    asyncio.run(test_refactoring_assistant())
