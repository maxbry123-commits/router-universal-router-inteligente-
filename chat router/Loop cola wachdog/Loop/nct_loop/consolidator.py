"""Fases 7 y 9: 3 niveles EROS y entrega, sin atribuir al modelo hechos no verificados."""

def consolidate(receipts:list[dict], stats:dict, *, verified:bool) -> dict:
    raw=[{'id':r['id'],'task_id':r['task_id'],'status':r['status']} for r in receipts]
    strategic={'completed':sum(r['status']=='PASS' for r in receipts),'total':len(receipts),
               'unverified':[r['id'] for r in receipts if r['status']!='PASS']}
    return {'tier3_receipts':raw,'tier2_progress':strategic,
            'tier1_digest':('VERIFIED' if verified else 'NOT_VERIFIED'),
            'metrics':stats}

def deliver(mission_id:str, results:dict, *, required_tasks:set[str]) -> dict:
    covered={r['task_id'] for r in results['receipts'] if r['status']=='PASS'}
    pass_all=results.get('triple_gate',{}).get('ok') is True and required_tasks.issubset(covered)
    return {'mission_id':mission_id,'status':'DONE_VERIFICADO' if pass_all else 'GAP',
            'receipts':results['receipts'],'triple_gate':results.get('triple_gate',{}),
            'summary':results.get('summary',{}),'missing_tasks':sorted(required_tasks-covered),
            'artifacts':results.get('artifacts',[])}
