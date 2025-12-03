#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import argparse
import re
from datetime import datetime, timezone
from typing import Dict, List, Tuple

import boto3
import botocore
import pandas as pd


GRAVITON_SPECIAL_FAMILIES = {
    # Graviton2/3 variações “fora do padrão <letras><número>g”
    "im4gn", "is4gen", "x2gd"
}

# Limiares simples para marcar “Antiga” por família primária
LEGACY_THRESHOLDS = {
    "t": 2,  # t1/t2 legadas
    "m": 4,  # m1–m4 legadas
    "c": 4,  # c1/c3/c4 legadas
    "r": 4,  # r3/r4 legadas
    "i": 2,  # i2 legada
    "d": 2,  # d2 legada
    # famílias não listadas caem na regra padrão (gen>=5 = atual)
}

FAMILY_RE = re.compile(r"^([a-z]+)(\d*)([a-z]*)$", re.IGNORECASE)

def parse_family_base(instance_type: str) -> Tuple[str, str, int, str]:
    """
    Ex.: 'm6g.large' -> ('m6g', 'm', 6, 'g')
         'c7gn.2xlarge' -> ('c7gn', 'c', 7, 'gn')
         'm5a.large' -> ('m5a', 'm', 5, 'a')
         't2.micro' -> ('t2', 't', 2, '')
    """
    family_part = instance_type.split(".")[0]
    m = FAMILY_RE.match(family_part)
    if not m:
        return family_part, family_part, 0, ""
    letters, digits, suffix = m.groups()
    gen = int(digits) if digits.isdigit() else 0
    return family_part, letters, gen, suffix

def is_graviton(family_base: str, prim: str, gen: int, suffix: str) -> bool:
    """
    Heurística:
    - famílias com padrão <letras><número>g / gd / gn → Graviton
      (ex.: m6g, m6gd, c7g, c7gn, r6g, t4g)
    - especiais: im4gn, is4gen, x2gd
    - evita falsos positivos de GPU (g4dn, g5), que começam com 'g'
    """
    fb = family_base.lower()
    if prim.lower() == "g":
        # g4dn/g5 = GPU, não Graviton
        return False

    if fb in GRAVITON_SPECIAL_FAMILIES:
        return True

    # Padrões comuns de Graviton
    if re.match(r"^[a-z]+[0-9]+g(n|d)?$", fb):
        return True

    return False

def is_legacy(prim: str, gen: int) -> bool:
    prim = prim.lower()
    if prim in LEGACY_THRESHOLDS and gen > 0:
        return gen <= LEGACY_THRESHOLDS[prim]
    # fallback conservador: se não conhecemos, considerar antigo só se geração 0/1/2
    return gen in (0, 1, 2)

def get_all_regions(session: boto3.session.Session) -> List[str]:
    ec2 = session.client("ec2")
    resp = ec2.describe_regions(AllRegions=True)
    return sorted([r["RegionName"] for r in resp["Regions"] if r.get("OptInStatus") in (None, "opt-in-not-required", "opted-in")])

def get_instances_for_region(session: boto3.session.Session, region: str) -> List[Dict]:
    ec2 = session.client("ec2", region_name=region)
    paginator = ec2.get_paginator("describe_instances")
    results = []
    for page in paginator.paginate():
        for res in page.get("Reservations", []):
            for inst in res.get("Instances", []):
                results.append(inst)
    return results

def get_name_tag(tags: List[Dict]) -> str:
    if not tags:
        return ""
    for t in tags:
        if t.get("Key") == "Name":
            return t.get("Value", "")
    return ""

def collect_inventory(profile: str, regions: List[str]) -> List[Dict]:
    sess = boto3.Session(profile_name=profile) if profile else boto3.Session()
    if regions == ["ALL"]:
        regions = get_all_regions(sess)

    rows = []
    for region in regions:
        try:
            instances = get_instances_for_region(sess, region)
        except botocore.exceptions.ClientError as e:
            # Sem permissão em alguma região/conta: segue adiante
            print(f"[{profile}] erro em {region}: {e}")
            continue

        for i in instances:
            itype = i.get("InstanceType", "")
            family_base, prim, gen, suffix = parse_family_base(itype)
            grav = is_graviton(family_base, prim, gen, suffix)
            legacy = is_legacy(prim, gen)

            state = i.get("State", {}).get("Name", "")
            launchtime = i.get("LaunchTime")
            if isinstance(launchtime, datetime):
                launchtime = launchtime.astimezone(timezone.utc).strftime("%Y-%m-%d %H:%M:%S %Z")
            name = get_name_tag(i.get("Tags"))

            rows.append({
                "Account(Profile)": profile or "default",
                "Region": region,
                "InstanceId": i.get("InstanceId"),
                "NameTag": name,
                "InstanceType": itype,
                "FamilyBase": family_base,
                "FamilyPrimary": prim,
                "Generation": gen,
                "Graviton": "Sim" if grav else "Não",
                "Status": "Antiga" if legacy else "Atual",
                "State": state,
                "LaunchTimeUTC": launchtime,
            })
    return rows

def main():
    ap = argparse.ArgumentParser(
        description="Inventário de EC2 por perfil/região, com detecção de gerações antigas e Graviton."
    )
    ap.add_argument(
        "--profiles",
        help="Perfis do AWS CLI separados por vírgula (ex.: Ticto,DeOnibus). Padrão: profile atual do ambiente.",
        default=""
    )
    ap.add_argument(
        "--regions",
        help="Regiões separadas por vírgula (ex.: us-east-1,sa-east-1). Use 'ALL' para todas. Padrão: ALL.",
        default="ALL"
    )
    ap.add_argument(
        "-o", "--out",
        help="Caminho do .xlsx de saída.",
        default=f"ec2_inventory_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
    )
    args = ap.parse_args()

    profiles = [p.strip() for p in args.profiles.split(",") if p.strip()] or [""]
    regions = [r.strip() for r in args.regions.split(",") if r.strip()] or ["ALL"]

    all_rows: List[Dict] = []
    for prof in profiles:
        print(f"Coletando perfil: {prof or 'default'} …")
        rows = collect_inventory(prof, regions)
        all_rows.extend(rows)

    if not all_rows:
        print("Nenhuma instância encontrada.")
        return

    df = pd.DataFrame(all_rows)
    # Ordenação amigável
    df = df.sort_values(["Account(Profile)", "Region", "Status", "Graviton", "FamilyBase", "InstanceId"])

    # Exporta para Excel com filtro na primeira linha
    with pd.ExcelWriter(args.out, engine="openpyxl") as writer:
        df.to_excel(writer, sheet_name="EC2_Inventory", index=False)
        ws = writer.sheets["EC2_Inventory"]
        # Congela header e ajusta largura
        ws.freeze_panes = "A2"
        for col in ws.columns:
            maxlen = max(len(str(c.value)) if c.value is not None else 0 for c in col)
            ws.column_dimensions[col[0].column_letter].width = min(max(12, maxlen + 2), 50)

    print(f"OK! Arquivo gerado: {args.out}")


if __name__ == "__main__":
    main()
