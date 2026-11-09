from pipeline.run import run

if __name__ == "__main__":
    result = run()
    base = result.scenarios["base"]
    print(f"rows={result.rows}")
    print(f"events={result.events}")
    print(f"high={','.join(result.high_variants)}")
    print(f"modeled_cents={base.modeled_cents}")
    print(f"contact_reduction={base.contact_reduction}")
