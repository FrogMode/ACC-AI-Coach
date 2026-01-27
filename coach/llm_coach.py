"""
LLM Coach Integration

Uses LLMs (OpenAI, Anthropic, or local models) to generate
natural language coaching feedback from telemetry analysis.
"""

import os
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from analysis.comparator import LapDelta, CornerDelta
from analysis.metrics import PerformanceMetrics
from analysis.segmenter import Corner


@dataclass
class CoachingFeedback:
    """Structured coaching feedback"""
    summary: str
    corner_tips: List[str]
    priority_focus: str
    encouragement: str


class LLMCoach:
    """
    Generates natural language coaching from telemetry analysis.
    
    Supports:
    - OpenAI (GPT-4, GPT-3.5)
    - Anthropic (Claude)
    - Local models via Ollama
    """
    
    def __init__(self, 
                 provider: str = "openai",
                 model: str = "gpt-4",
                 api_key: Optional[str] = None):
        """
        Initialize the LLM coach.
        
        Args:
            provider: "openai", "anthropic", or "ollama"
            model: Model name (e.g., "gpt-4", "claude-3-opus", "llama2")
            api_key: API key (or set via environment variable)
        """
        self.provider = provider
        self.model = model
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        
        self._client = None
    
    def _get_client(self):
        """Lazy-load the API client"""
        if self._client is not None:
            return self._client
        
        if self.provider == "openai":
            from openai import OpenAI
            self._client = OpenAI(api_key=self.api_key)
        elif self.provider == "anthropic":
            import anthropic
            self._client = anthropic.Anthropic(api_key=self.api_key)
        elif self.provider == "ollama":
            # Ollama uses HTTP API, no client needed
            pass
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
        
        return self._client
    
    def _call_llm(self, prompt: str, system_prompt: str = "") -> str:
        """Call the LLM with the given prompt"""
        if self.provider == "openai":
            client = self._get_client()
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            
            response = client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                max_tokens=1000,
            )
            return response.choices[0].message.content
        
        elif self.provider == "anthropic":
            client = self._get_client()
            response = client.messages.create(
                model=self.model,
                max_tokens=1000,
                system=system_prompt if system_prompt else "You are a helpful racing coach.",
                messages=[{"role": "user", "content": prompt}],
            )
            return response.content[0].text
        
        elif self.provider == "ollama":
            import requests
            response = requests.post(
                "http://localhost:11434/api/generate",
                json={
                    "model": self.model,
                    "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
                    "stream": False,
                },
            )
            return response.json()["response"]
        
        else:
            raise ValueError(f"Unknown provider: {self.provider}")
    
    def analyze_lap_comparison(self, 
                                delta: LapDelta,
                                track_name: str = "",
                                car_name: str = "") -> CoachingFeedback:
        """
        Generate coaching feedback from a lap comparison.
        
        Args:
            delta: LapDelta from comparing two laps
            track_name: Name of the track
            car_name: Name of the car
            
        Returns:
            CoachingFeedback with natural language tips
        """
        system_prompt = """You are an expert sim racing coach specializing in GT3 racing. 
You analyze telemetry data and provide clear, actionable feedback to help drivers improve.
Be specific and technical, but explain concepts clearly.
Focus on the most impactful improvements first.
Be encouraging but honest about areas needing work."""
        
        # Build the analysis prompt
        prompt_parts = [
            f"Analyze this lap comparison for {track_name} in a {car_name}:" if track_name else "Analyze this lap comparison:",
            f"\nTotal time delta: {delta.total_delta_ms:+.0f}ms",
        ]
        
        if delta.biggest_time_loss:
            prompt_parts.append(f"Biggest time loss: {delta.biggest_time_loss}")
        if delta.biggest_time_gain:
            prompt_parts.append(f"Biggest time gain: {delta.biggest_time_gain}")
        
        prompt_parts.append("\nCorner-by-corner breakdown:")
        for cd in delta.corner_deltas[:10]:  # Limit to 10 corners
            prompt_parts.append(
                f"- {cd.corner.name}: {cd.total_delta_ms:+.0f}ms "
                f"(entry speed delta: {cd.entry_speed_delta:+.1f} km/h, "
                f"apex: {cd.apex_speed_delta:+.1f} km/h, "
                f"exit: {cd.exit_speed_delta:+.1f} km/h)"
            )
            if cd.issues:
                prompt_parts.append(f"  Issues: {', '.join(cd.issues)}")
        
        prompt_parts.append("""
Please provide:
1. A brief summary of overall performance (2-3 sentences)
2. Specific tips for the 2-3 corners where time is being lost
3. One key focus area for the next session
4. A brief encouragement""")
        
        prompt = "\n".join(prompt_parts)
        
        # Call LLM
        try:
            response = self._call_llm(prompt, system_prompt)
            return self._parse_coaching_response(response)
        except Exception as e:
            # Fallback to template-based response
            return self._generate_template_feedback(delta)
    
    def generate_corner_tip(self, 
                            corner: Corner,
                            corner_delta: CornerDelta,
                            context: str = "") -> str:
        """Generate a specific tip for improving a corner"""
        system_prompt = """You are a racing coach giving a quick tip for a specific corner.
Be concise (1-2 sentences) and actionable."""
        
        prompt = f"""Corner: {corner.name}
Type: {corner.corner_type}
Your performance:
- Time delta: {corner_delta.total_delta_ms:+.0f}ms
- Entry speed delta: {corner_delta.entry_speed_delta:+.1f} km/h
- Apex speed delta: {corner_delta.apex_speed_delta:+.1f} km/h  
- Exit speed delta: {corner_delta.exit_speed_delta:+.1f} km/h
Issues detected: {', '.join(corner_delta.issues) if corner_delta.issues else 'None'}

Give one specific, actionable tip to improve this corner."""
        
        try:
            return self._call_llm(prompt, system_prompt)
        except Exception:
            return self._generate_template_corner_tip(corner_delta)
    
    def generate_realtime_callout(self,
                                   upcoming_corner: Corner,
                                   historical_delta: Optional[CornerDelta] = None,
                                   current_speed: float = 0) -> str:
        """
        Generate a real-time voice callout for an upcoming corner.
        
        This should be short (< 3 seconds when spoken).
        
        Args:
            upcoming_corner: The corner the driver is approaching
            historical_delta: How they performed at this corner previously
            current_speed: Current speed in km/h
            
        Returns:
            Short callout string for TTS
        """
        # For real-time, use templates for speed (no LLM latency)
        if historical_delta is None:
            return f"{upcoming_corner.name}, brake at marker"
        
        if historical_delta.total_delta_ms > 100:
            # Lost time here before
            if historical_delta.entry_speed_delta < -5:
                return f"{upcoming_corner.name}, carry more speed in"
            elif historical_delta.exit_speed_delta < -5:
                return f"{upcoming_corner.name}, earlier throttle"
            else:
                return f"{upcoming_corner.name}, focus here"
        elif historical_delta.total_delta_ms < -100:
            # Gained time here
            return f"{upcoming_corner.name}, good corner, keep it up"
        else:
            return f"{upcoming_corner.name}"
    
    def _parse_coaching_response(self, response: str) -> CoachingFeedback:
        """Parse LLM response into structured feedback"""
        # Simple parsing - in production, could use structured output
        lines = response.strip().split('\n')
        
        # Try to extract sections
        summary = ""
        corner_tips = []
        priority = ""
        encouragement = ""
        
        current_section = "summary"
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            lower = line.lower()
            
            if "tip" in lower or "corner" in lower and ":" in line:
                current_section = "tips"
            elif "focus" in lower or "priority" in lower:
                current_section = "priority"
            elif "encouragement" in lower or "keep" in lower:
                current_section = "encouragement"
            
            if current_section == "summary" and len(summary) < 500:
                summary += line + " "
            elif current_section == "tips":
                corner_tips.append(line)
            elif current_section == "priority":
                priority = line
            elif current_section == "encouragement":
                encouragement = line
        
        return CoachingFeedback(
            summary=summary.strip() or "Analysis complete.",
            corner_tips=corner_tips[:5],  # Max 5 tips
            priority_focus=priority or "Focus on smooth inputs.",
            encouragement=encouragement or "Keep pushing! Every lap is progress.",
        )
    
    def _generate_template_feedback(self, delta: LapDelta) -> CoachingFeedback:
        """Generate feedback using templates when LLM is unavailable"""
        summary = f"You're {abs(delta.total_delta_ms)/1000:.2f}s "
        summary += "slower" if delta.total_delta_ms > 0 else "faster"
        summary += " than the reference lap."
        
        corner_tips = []
        for cd in sorted(delta.corner_deltas, key=lambda x: x.total_delta_ms, reverse=True)[:3]:
            if cd.total_delta_ms > 50:
                tip = f"{cd.corner.name}: "
                if cd.entry_speed_delta < -5:
                    tip += "Carry more speed into the corner."
                elif cd.exit_speed_delta < -5:
                    tip += "Get on the throttle earlier."
                else:
                    tip += "Work on your line through this corner."
                corner_tips.append(tip)
        
        priority = delta.biggest_time_loss or "Overall consistency"
        
        return CoachingFeedback(
            summary=summary,
            corner_tips=corner_tips,
            priority_focus=f"Focus on improving {priority}",
            encouragement="Keep practicing! Consistent laps lead to faster times.",
        )
    
    def _generate_template_corner_tip(self, corner_delta: CornerDelta) -> str:
        """Generate corner tip using templates"""
        if corner_delta.entry_speed_delta < -5:
            return "Try braking later and carrying more speed into the corner."
        elif corner_delta.apex_speed_delta < -5:
            return "You might be over-slowing. Trust the car's grip at the apex."
        elif corner_delta.exit_speed_delta < -5:
            return "Focus on getting on the power earlier as you unwind the steering."
        else:
            return "Work on finding a smoother line through this corner."
