"""R1 Critic Agent prototype (midpoint, Nov 2026).

Reviews a Drafter's GSN-style argument bundle against the supplied evidence
package and checker results. It reports problems; it never decides whether
the robot was physically safe, never edits evidence and never invents
observations.
"""
from .critic import review, CRITIC_VERSION  # noqa: F401
