"""LayerRunner: cadena de gobernanza completa por nodo."""
from wordflow_loop.contracts import Evidence, LayerResult, NodeContract, Status
from wordflow_loop.ledger import verify_ledger
from wordflow_loop.runner import LayerRunner


def _node(**kw):
    args = dict(node_id="n1", layer="L", literal="do x",
                literal_sha256="", timeout_ms=10_000)
    args.update(kw)
    args["literal_sha256"] = NodeContract.build(
        **{k: v for k, v in args.items() if k != "literal_sha256"}).literal_sha256
    return NodeContract(**args)


def test_pass_requires_governance_chain_and_evidence():
    node = _node()

    def exec_ok(node, ctx):
        return LayerResult(node_id=node.node_id, layer=node.layer,
                           status=Status.PASS,
                           evidence=[Evidence(kind="test", ref="/tmp/ev.txt")])

    runner = LayerRunner(exec_ok)
    res = runner.run([node])
    assert res["n1"].status == Status.PASS
    assert verify_ledger(runner.ledger)


def test_pass_without_evidence_fails_via_verifier():
    node = _node()
    runner = LayerRunner(lambda n, c: LayerResult(node_id=n.node_id, layer=n.layer,
                                                  status=Status.PASS))
    res = runner.run([node])
    assert res["n1"].status == Status.FAIL
    assert any("evidence" in g for g in res["n1"].gaps)


def test_sheriff_blocks_bad_literal_hash():
    node = _node()
    node = NodeContract(**{**node.__dict__, "literal_sha256": "0" * 64})
    runner = LayerRunner(lambda n, c: LayerResult(node_id=n.node_id, layer=n.layer, status=Status.PASS))
    res = runner.run([node])
    assert res["n1"].status == Status.BLOCKED


def test_mutation_on_readonly_denied():
    node = _node(mutation=False)
    def exec_mut(node, ctx):
        return LayerResult(node_id=node.node_id, layer=node.layer, status=Status.PASS,
                           actions=["write"], touched_paths=["/x"],
                           evidence=[Evidence(kind="t", ref="/r")])
    runner = LayerRunner(exec_mut)
    res = runner.run([node])
    assert res["n1"].status == Status.FAIL


def test_dependency_order_enforced():
    a = _node(node_id="a")
    b = _node(node_id="b", depends_on=("a",))
    seen = []
    def exec_track(n, c):
        seen.append(n.node_id)
        return LayerResult(node_id=n.node_id, layer=n.layer, status=Status.PASS,
                           evidence=[Evidence(kind="t", ref="/r")])
    runner = LayerRunner(exec_track)
    res = runner.run([b, a])
    assert seen == ["a", "b"]
    assert res["b"].status == Status.PASS
