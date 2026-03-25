import json
from datetime import datetime, date
from extensions import db
from models.models import Profile, DomainLevel, KnowledgeNode, Milestone
from services import ai as ai_service


def get_or_create_profile():
    profile = Profile.query.first()
    if not profile:
        profile = Profile()
        db.session.add(profile)
        db.session.commit()
    return profile


def update_streak(profile):
    today = date.today().isoformat()
    if profile.last_active_date == today:
        return
    yesterday = (date.today().replace(day=date.today().day - 1)).isoformat()
    if profile.last_active_date == yesterday:
        profile.day_streak += 1
    else:
        profile.day_streak = 1
    profile.last_active_date = today
    db.session.commit()


def add_xp(profile, domain_name, amount):
    profile.total_xp += amount
    # Update global level (every 500 XP)
    profile.global_level = max(1, profile.total_xp // 500 + 1)

    # Update domain level
    dl = DomainLevel.query.filter_by(domain=domain_name).first()
    if not dl:
        dl = DomainLevel(domain=domain_name)
        db.session.add(dl)
    dl.xp += amount
    dl.tasks_completed += 1
    # Level up: 100 XP per level, scaling
    xp_needed = dl.level * 100
    if dl.xp >= xp_needed:
        dl.xp -= xp_needed
        dl.level += 1
        dl.xp_to_next = dl.level * 100
        # Create milestone for level up
        m = Milestone(
            title=f"Level {dl.level} in {domain_name}",
            description=f"You reached level {dl.level} in {domain_name}. The tasks are about to get harder.",
            milestone_type="level_up",
            domain=domain_name,
        )
        db.session.add(m)
    db.session.commit()


def ensure_domain(domain_name):
    dl = DomainLevel.query.filter_by(domain=domain_name).first()
    if not dl:
        dl = DomainLevel(domain=domain_name)
        db.session.add(dl)
        db.session.commit()
    return dl


def update_knowledge_graph(concepts, domain):
    for concept in concepts:
        if not concept or len(concept) < 2:
            continue
        node = KnowledgeNode.query.filter_by(concept=concept).first()
        if node:
            node.evidence_count += 1
            node.mastery_score = min(1.0, node.mastery_score + 0.1)
            node.last_touched = datetime.utcnow()
        else:
            node = KnowledgeNode(concept=concept, domain=domain)
            db.session.add(node)
    db.session.commit()

    # Connect related concepts
    if len(concepts) > 1:
        for i, c1 in enumerate(concepts):
            node1 = KnowledgeNode.query.filter_by(concept=c1).first()
            if not node1:
                continue
            conns = node1.get_connections()
            for c2 in concepts[i+1:]:
                if c2 not in conns:
                    conns.append(c2)
            node1.connections = json.dumps(conns[:20])
        db.session.commit()


def apply_debrief_results(profile, task, eval_data):
    # Update strengths
    existing_strengths = profile.get_strengths()
    for s in eval_data.get("new_strengths", []):
        if s and s not in existing_strengths:
            existing_strengths.append(s)
    profile.strengths = json.dumps(existing_strengths[:20])

    # Update weaknesses
    existing_weaknesses = profile.get_weaknesses()
    for w in eval_data.get("new_weaknesses", []):
        if w and w not in existing_weaknesses:
            existing_weaknesses.append(w)
    profile.weaknesses = json.dumps(existing_weaknesses[:20])

    # Update knowledge graph
    concepts = eval_data.get("new_concepts", [])
    if concepts:
        update_knowledge_graph(concepts, task.domain)

    # Update domains list
    domains = profile.get_domains()
    if task.domain and task.domain not in domains:
        domains.append(task.domain)
        profile.domains = json.dumps(domains)

    db.session.commit()


def merge_profile_from_cold_start(profile, extracted):
    if not extracted:
        return
    if extracted.get("interests"):
        profile.inferred_interests = json.dumps(extracted["interests"])
    if extracted.get("communication_style"):
        profile.communication_style = extracted["communication_style"]
    if extracted.get("vocabulary_level"):
        profile.vocabulary_level = extracted["vocabulary_level"]
    if extracted.get("learning_style"):
        profile.learning_style = extracted["learning_style"]
    if extracted.get("strengths"):
        profile.strengths = json.dumps(extracted["strengths"])
    if extracted.get("weaknesses"):
        profile.weaknesses = json.dumps(extracted["weaknesses"])
    if extracted.get("domains"):
        profile.domains = json.dumps(extracted["domains"])
        for d in extracted["domains"]:
            ensure_domain(d)
    if extracted.get("ai_observations"):
        profile.ai_observations = extracted["ai_observations"]
    profile.cold_start_complete = True
    db.session.commit()


def get_knowledge_graph_data():
    nodes = KnowledgeNode.query.all()
    node_list = []
    edge_list = []
    seen_edges = set()
    for n in nodes:
        node_list.append({
            "id": n.concept,
            "label": n.concept,
            "domain": n.domain,
            "mastery": n.mastery_score,
            "evidence": n.evidence_count,
        })
        for conn in n.get_connections():
            edge_key = tuple(sorted([n.concept, conn]))
            if edge_key not in seen_edges:
                seen_edges.add(edge_key)
                edge_list.append({"source": n.concept, "target": conn})
    return {"nodes": node_list, "edges": edge_list}
