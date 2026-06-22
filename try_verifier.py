from src.retrieval_service import get_evidence_for_claim
from src.verifier import verify_claim

test_claims = [
    "Lemon water cures cancer.",                       # expect: contradicted
    "The Eiffel Tower is 330 meters tall.",            # expect: supported
    "Marie Curie won the Nobel Prize in Literature.",  # expect: contradicted
    "Eating one carrot makes you invisible.",          # expect: not_enough_evidence
]

print("Loading models (first run downloads ~330 MB)...\n")

for claim in test_claims:
    evidence = get_evidence_for_claim(claim, top_k=3)
    verdict, confidence, scored = verify_claim(claim, evidence)

    print(f"CLAIM: {claim}")
    print(f"   VERDICT: {verdict.value}   (confidence {confidence:.2f})")
    top = scored[0]
    print(f"   top evidence [{top.support_type}] {top.source_title}")
    print(f"      {top.text[:70]}...")
    print()