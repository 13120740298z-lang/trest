from __future__ import annotations

from .models import AstrologyCommonParams, AstrologyPoint, AstrologyStats, ReportAstrology, ReportMbti, ReportProfile, ReportSection, ReportTarot, TarotCard
from .mbti_assets import load_mbti_assets


_SIGN_ZH = {
    "Ari": "白羊座",
    "Tau": "金牛座",
    "Gem": "双子座",
    "Can": "巨蟹座",
    "Leo": "狮子座",
    "Vir": "处女座",
    "Lib": "天秤座",
    "Sco": "天蝎座",
    "Sag": "射手座",
    "Cap": "摩羯座",
    "Aqu": "水瓶座",
    "Pis": "双鱼座",
}


def _sign_label(sign: str | None) -> str:
    if not sign:
        return "未知星座"
    return _SIGN_ZH.get(sign, sign)


def build_profile(*, chart: dict, mbti: str | None) -> ReportProfile:
    sun_sign = _sign_label(chart.get("sun", {}).get("sign"))
    asc_sign = _sign_label(chart.get("ascendant", {}).get("sign"))
    moon_sign = _sign_label(chart.get("moon", {}).get("sign"))

    summary = f"你给人的第一印象更偏向 {asc_sign}，核心驱动力由 {sun_sign} 主导，情绪模式带有 {moon_sign} 的底色。"
    traits = [sun_sign, asc_sign, moon_sign]
    strengths = ["目标感", "行动力", "自我觉察"]
    blind_spots = ["过度用力", "情绪压抑", "节奏失衡"]

    if mbti:
        traits.append(mbti.upper())

    return ReportProfile(
        summary=summary,
        traits=traits,
        strengths=strengths,
        blind_spots=blind_spots,
    )


def build_astrology(*, chart: dict, highlights: list[str]) -> ReportAstrology:
    sun = chart.get("sun", {})
    moon = chart.get("moon", {})
    asc = chart.get("ascendant", {})

    common = AstrologyCommonParams(
        local_datetime=chart.get("iso_formatted_local_datetime"),
        utc_datetime=chart.get("iso_formatted_utc_datetime"),
        city=chart.get("city"),
        nation=chart.get("nation"),
        lat=chart.get("lat"),
        lon=chart.get("lng"),
        timezone=chart.get("tz_str"),
        zodiac_type=chart.get("zodiac_type"),
        houses_system_name=chart.get("houses_system_name"),
        perspective_type=chart.get("perspective_type"),
    )

    def house_num(v: str | None) -> int | None:
        if not v or not isinstance(v, str):
            return None
        if v.endswith("_House"):
            prefix = v.removesuffix("_House")
            mapping = {
                "First": 1,
                "Second": 2,
                "Third": 3,
                "Fourth": 4,
                "Fifth": 5,
                "Sixth": 6,
                "Seventh": 7,
                "Eighth": 8,
                "Ninth": 9,
                "Tenth": 10,
                "Eleventh": 11,
                "Twelfth": 12,
            }
            return mapping.get(prefix)
        return None

    point_keys = [
        "sun",
        "moon",
        "mercury",
        "venus",
        "mars",
        "jupiter",
        "saturn",
        "uranus",
        "neptune",
        "pluto",
        "ascendant",
        "medium_coeli",
        "descendant",
        "imum_coeli",
    ]
    points: list[AstrologyPoint] = []
    for key in point_keys:
        p = chart.get(key)
        if not isinstance(p, dict):
            continue
        points.append(
            AstrologyPoint(
                key=key,
                name=p.get("name"),
                sign=p.get("sign"),
                emoji=p.get("emoji"),
                element=p.get("element"),
                quality=p.get("quality"),
                house=p.get("house"),
                house_num=house_num(p.get("house")),
                retrograde=p.get("retrograde"),
                position=p.get("position"),
            )
        )

    def _count(values: list[str]) -> dict[str, int]:
        out: dict[str, int] = {}
        for v in values:
            out[v] = out.get(v, 0) + 1
        return out

    element_vals = [p.element for p in points if p.element]
    quality_vals = [p.quality for p in points if p.quality]

    yin = 0
    yang = 0
    for e in element_vals:
        if e in ("Fire", "Air"):
            yang += 1
        elif e in ("Earth", "Water"):
            yin += 1

    stats = AstrologyStats(
        element_counts=_count(element_vals),
        quality_counts=_count(quality_vals),
        yin_yang_counts={"yin": yin, "yang": yang},
    )

    sections = [
        ReportSection(
            title="关键落点",
            content="；".join(
                [
                    f"太阳在 {_sign_label(sun.get('sign'))}（第 {sun.get('house', '')} 宫）",
                    f"月亮在 {_sign_label(moon.get('sign'))}（第 {moon.get('house', '')} 宫）",
                    f"上升在 {_sign_label(asc.get('sign'))}",
                ]
            ),
        ),
        ReportSection(
            title="长期基调",
            content="这一层用于描述长期性格与人生叙事的倾向。第一版先用核心落点给出概括，后续可加入相位与宫位主题的更精细规则。",
        ),
    ]

    return ReportAstrology(
        raw_chart=chart,
        highlights=highlights,
        common_params=common,
        points=points,
        stats=stats,
        interpretation=sections,
    )


def build_tarot(*, spread, cards: list[TarotCard], domain: str | None) -> ReportTarot:
    title = "塔罗解读"
    if spread.type == "single":
        title = "单张：当前状态与建议"
    if spread.type == "three":
        title = "三张：状态-阻碍-建议"

    joined = "\n".join([f"- {c.name}（{ '正位' if c.orientation=='upright' else '逆位' }）：{c.meaning}" for c in cards])
    sections = [
        ReportSection(title=title, content=joined),
        ReportSection(
            title="落地提醒",
            content="把牌义当作行动线索而不是命运裁决：你可以用它来做“下一步怎么做更顺”的微调。",
        ),
    ]

    return ReportTarot(spread=spread, cards=cards, interpretation=sections)


def build_mbti(*, mbti: str) -> ReportMbti:
    t = mbti.upper()
    assets = load_mbti_assets()

    def side(code: str) -> str:
        s = assets.sides.get(code)
        if not s:
            return code
        return f"{s.label}"

    dims = [
        ("能量", t[0] if len(t) > 0 else ""),
        ("信息", t[1] if len(t) > 1 else ""),
        ("决策", t[2] if len(t) > 2 else ""),
        ("执行", t[3] if len(t) > 3 else ""),
    ]
    dim_lines = [f"- {name}：{side(code)}" for name, code in dims if code]

    example_lines: list[str] = []
    for _, code in dims:
        s = assets.sides.get(code)
        if not s:
            continue
        for ex in s.examples[:2]:
            example_lines.append(f"- {code}：{ex}")

    sections = [
        ReportSection(title="四维倾向", content="\n".join(dim_lines) if dim_lines else t),
        ReportSection(
            title="来自数据集的示例表达",
            content="\n".join(example_lines) if example_lines else "（暂无示例）",
        ),
        ReportSection(
            title="使用方式",
            content="这些示例用于“对齐表达风格”，不是固定结论。你可以在继续追问时，用它来约束输出语气与决策偏好。",
        ),
    ]
    return ReportMbti(type=t, interpretation=sections)


def build_action_guide(*, domain: str | None) -> list[str]:
    base = [
        "把目标拆成一个“今天能完成的最小动作”，先做完再优化。",
        "为自己预留 30 分钟的安静时间：记录情绪波动与触发点。",
        "如果卡住，先写出 3 个可选方案，再选择风险最低的一个先验证。",
    ]
    if domain:
        base.insert(0, f"围绕“{domain}”只做一件最关键的事：先明确你真正想要的结果。")
    return base[:5]


def build_followups(*, domain: str | None) -> list[str]:
    qs = [
        "你最近最反复出现的情绪或困扰是什么？",
        "你希望在接下来 30 天里具体改变哪一个行为？",
        "你现在最需要的是“更清晰的目标”还是“更稳定的执行节奏”？",
    ]
    if domain:
        qs.insert(0, f"在“{domain}”上，你最想要的具体结果是什么？")
    return qs[:5]
