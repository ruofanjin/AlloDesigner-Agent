from .boundary import BoundaryAgent
from .critic import CriticAgent
from .ensemble import EnsembleAgent
from .librarian import LibrarianAgent
from .physics import PhysicsAgent
from .pocket_eval import PocketEvalAgent
from .ranking import RankingAgent
from .residue_prior import ResiduePriorAgent

STAGE_AGENTS = {
    "boundary": BoundaryAgent,
    "residue_prior": ResiduePriorAgent,
    "ensemble_enrichment": EnsembleAgent,
    "physics_sampling": PhysicsAgent,
    "pocket_evaluation": PocketEvalAgent,
    "candidate_ranking": RankingAgent,
}

__all__ = [
    "STAGE_AGENTS",
    "BoundaryAgent",
    "ResiduePriorAgent",
    "EnsembleAgent",
    "PhysicsAgent",
    "PocketEvalAgent",
    "RankingAgent",
    "LibrarianAgent",
    "CriticAgent",
]
