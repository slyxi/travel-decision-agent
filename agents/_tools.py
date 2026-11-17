"""
Agent Tools — 出行决策 Agent（高德地图 Web 服务）
=================================================

私有模块（文件名以 `_` 开头，不会映射为公开路由）。

本文件只做一件事：把高德地图 Web 服务的能力封装成 OpenAI Agents SDK 的工具。
所有密钥只从环境变量 `AMAP_API_KEY` 读取，任何地方都不硬编码 Key。

工具清单
--------
1. geocode_address        地址 / 地标名 → 经纬度（"红莲南路地铁站" → "116.33,39.87"）
2. search_nearby_places   以一点为中心做周边检索（找商场、找某个品牌门店）
3. calc_distance          计算两点之间的距离（直线 / 驾车）
4. find_malls_with_brands 【核心】一次调用完成：定位 → 找附近商场 → 逐商场核对品牌 → 按条件排序

调用原则（对应课程 9.2 的"工具描述应明确调用条件、输入、输出和限制"）：
- 用户给出"文字地址 / 地标"时，必须先 geocode_address，不允许模型自己编造经纬度。
- 用户问"附近有哪些商场 / 某品牌在哪"时用 search_nearby_places。
- 用户问"哪个更近 / 距离多少"时用 calc_distance，距离一律来自接口返回值。
- 用户提出"既要 A 又要 B、要近的商场"这类组合条件时，直接用 find_malls_with_brands。
"""

from __future__ import annotations

import json
import os
from typing import Annotated, Any

import httpx
from agents import function_tool

AMAP_BASE = "https://restapi.amap.com/v3"
HTTP_TIMEOUT = 20.0

# 高德 POI 分类码：060100 = 综合市场/购物中心（商场）
MALL_TYPES = "060100"


# ==========================================================================
# 内部工具函数
# ==========================================================================
class AmapError(RuntimeError):
    """高德接口返回非成功状态时抛出，message 直接回给模型，便于它向用户解释原因。"""


def _amap_get(path: str, params: dict[str, Any]) -> dict[str, Any]:
    """统一的高德 GET 请求：注入 Key、校验 status、返回 JSON。"""
    key = os.getenv("AMAP_API_KEY", "").strip()
    if not key:
        raise AmapError(
            "缺少环境变量 AMAP_API_KEY。请在高德开放平台创建应用并添加「Web 服务」类型的 Key，"
            "写入 .env 后重启服务。"
        )

    query = {k: v for k, v in params.items() if v not in (None, "")}
    query["key"] = key
    query["output"] = "JSON"

    try:
        with httpx.Client(timeout=HTTP_TIMEOUT) as client:
            resp = client.get(f"{AMAP_BASE}{path}", params=query)
            resp.raise_for_status()
            data = resp.json()
    except httpx.HTTPError as exc:  # 网络层失败
        raise AmapError(f"调用高德接口 {path} 失败：{exc}") from exc

    if str(data.get("status")) != "1":
        raise AmapError(
            f"高德接口 {path} 返回错误：{data.get('info')}（infocode={data.get('infocode')}）"
        )
    return data


def _fmt_location(location: Any) -> str:
    """高德返回的 location 可能是 '116.3,39.8'，也可能是对象；统一成字符串。"""
    if isinstance(location, str):
        return location
    if isinstance(location, dict):
        return f"{location.get('lng')},{location.get('lat')}"
    return ""


def _meters(text: Any) -> float:
    """把高德返回的 distance（字符串，单位米）转成 float。"""
    try:
        return float(text)
    except (TypeError, ValueError):
        return float("inf")


def _human_distance(meters: float) -> str:
    if meters == float("inf"):
        return "未知"
    return f"{meters / 1000:.2f} 公里" if meters >= 1000 else f"{int(meters)} 米"


def _geocode(address: str, city: str = "") -> dict[str, Any]:
    """地址 → 经纬度，返回第一个候选。"""
    data = _amap_get("/geocode/geo", {"address": address, "city": city})
    geocodes = data.get("geocodes") or []
    if not geocodes:
        raise AmapError(f"高德未找到「{address}」的位置，请换一个更明确的地标或补充城市名。")
    g = geocodes[0]
    return {
        "formatted_address": g.get("formatted_address") or address,
        "province": g.get("province"),
        "city": g.get("city") or g.get("province"),
        "adcode": g.get("adcode"),
        "location": _fmt_location(g.get("location")),
    }


def _around(location: str, keywords: str, radius: int, types: str = "") -> list[dict[str, Any]]:
    """周边检索，返回精简后的 POI 列表。"""
    data = _amap_get(
        "/place/around",
        {
            "location": location,
            "keywords": keywords,
            "types": types,
            "radius": radius,
            "offset": 25,
            "page": 1,
            "extensions": "all",
        },
    )
    pois = data.get("pois") or []
    out = []
    for p in pois:
        if not isinstance(p, dict):
            continue
        out.append(
            {
                "id": p.get("id"),
                "name": p.get("name"),
                "type": p.get("type"),
                "address": p.get("address") if isinstance(p.get("address"), str) else "",
                "location": _fmt_location(p.get("location")),
                "distance_m": _meters(p.get("distance")),
                "tel": p.get("tel") if isinstance(p.get("tel"), str) else "",
            }
        )
    out.sort(key=lambda x: x["distance_m"])
    return out


# ==========================================================================
# 工具 1：地址 / 地标 → 经纬度
# ==========================================================================
@function_tool
def geocode_address(
    address: Annotated[str, "用户给出的地点描述，例如「红莲南路地铁站」「北京西站」「上海人民广场」"],
    city: Annotated[str, "可选的城市名或城市编码，例如「北京」。不确定就传空字符串"] = "",
) -> str:
    """把文字地址、地铁站名或地标解析成经纬度坐标。

    何时调用：用户只给了「我在哪儿」这类文字位置，而后续所有检索都必须用经纬度时，先调用本工具。
    输入：address（必填，中文地标名），city（可选，用于消歧，重名地点时建议提供）。
    输出：JSON，包含 formatted_address / city / location（"经度,纬度"）。
    限制：若返回错误信息，说明地址不够明确，应先向用户追问城市或更具体的地标，不要自己编造坐标。
    """
    try:
        return json.dumps(_geocode(address, city), ensure_ascii=False)
    except AmapError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


# ==========================================================================
# 工具 2：周边检索
# ==========================================================================
@function_tool
def search_nearby_places(
    location: Annotated[str, "中心点坐标，格式为「经度,纬度」，必须是 geocode_address 返回的值"],
    keywords: Annotated[str, "搜索关键词，例如「商场」「购物中心」「倍轻松」「西厅村屋」"],
    radius: Annotated[int, "检索半径，单位米。默认 5000，找单个门店时建议 1000~3000"] = 5000,
    types: Annotated[str, "高德 POI 分类码。找商场固定传 060100；按品牌名找门店传空字符串"] = "",
) -> str:
    """以某个坐标为圆心做周边检索，返回按距离升序排列的 POI 列表。

    何时调用：用户问「附近有哪些商场」「××品牌在哪」，或需要核对某个品牌门店位置时。
    输入：location（必填，"经度,纬度"）、keywords（必填）、radius（可选，米）、types（可选，分类码）。
    输出：JSON 数组，每项含 name / address / location / distance_m / tel。
    限制：location 必须是地理编码或上一次检索返回的真实坐标；结果为 0 条时如实告知用户，不要臆造店铺。
    """
    try:
        pois = _around(location, keywords, radius, types)
        return json.dumps(
            {"count": len(pois), "pois": pois[:20]}, ensure_ascii=False
        )
    except AmapError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


# ==========================================================================
# 工具 3：距离计算
# ==========================================================================
@function_tool
def calc_distance(
    origin: Annotated[str, "起点坐标，格式为「经度,纬度」"],
    destination: Annotated[str, "终点坐标，格式为「经度,纬度」"],
    mode: Annotated[str, "距离类型：'straight' 直线距离（默认）或 'driving' 驾车距离"] = "straight",
) -> str:
    """计算两个坐标点之间的距离，用于比较「哪个商场更近」。

    何时调用：用户明确要比较距离、或需要给出「近/远」结论时。
    输入：origin、destination（均为 "经度,纬度"），mode（straight 或 driving）。
    输出：JSON，包含 distance_m / distance_text（如 "3.21 公里"）/ duration_text（驾车时）。
    限制：所有距离必须以本工具返回值为准，禁止模型自行估算。单点直线距离优先用 straight。
    """
    try:
        if mode == "driving":
            data = _amap_get(
                "/direction/driving",
                {"origin": origin, "destination": destination, "extensions": "base"},
            )
            paths = ((data.get("route") or {}).get("paths")) or []
            if not paths:
                raise AmapError("高德未返回可用的驾车路线。")
            meters = float(paths[0].get("distance") or 0)
            seconds = float(paths[0].get("duration") or 0)
            return json.dumps(
                {
                    "mode": "driving",
                    "distance_m": meters,
                    "distance_text": _human_distance(meters),
                    "duration_text": f"约 {seconds / 60:.0f} 分钟" if seconds else "未知",
                },
                ensure_ascii=False,
            )

        data = _amap_get(
            "/distance", {"origins": origin, "destination": destination, "type": 1}
        )
        results = data.get("results") or []
        meters = _meters(results[0].get("distance")) if results else float("inf")
        if meters == float("inf"):
            raise AmapError("高德未返回距离结果。")
        return json.dumps(
            {
                "mode": "straight",
                "distance_m": meters,
                "distance_text": _human_distance(meters),
            },
            ensure_ascii=False,
        )
    except AmapError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)


# ==========================================================================
# 工具 4（核心）：按「多品牌 + 距离」找商场
# ==========================================================================
@function_tool
def find_malls_with_brands(
    origin_address: Annotated[str, "用户的位置描述，例如「红莲南路地铁站附近」"],
    brands: Annotated[list[str], "用户要求商场里必须有的品牌或店铺关键词，例如 ['倍轻松', '西厅村屋']"],
    city: Annotated[str, "可选城市名，用于地址消歧，例如「北京」"] = "",
    mall_radius: Annotated[int, "以用户位置为中心搜索商场的半径，单位米，默认 5000"] = 5000,
    brand_radius: Annotated[int, "在商场内部核对品牌的半径，单位米，默认 800"] = 800,
) -> str:
    """【出行决策核心工具】一次完成：定位 → 搜索附近商场 → 逐商场核对品牌 → 按匹配与距离排序。

    何时调用：用户提出「我在 X 附近，想找既有 A 又有 B 的商场，要近的」这类组合诉求时，
              优先调用本工具，而不是自己一步步拼装其他工具。

    输入：
        origin_address —— 用户位置（中文地址或地标名）；
        brands         —— 必须存在的品牌/店铺关键词列表；
        city           —— 可选，地址消歧；
        mall_radius    —— 商场搜索半径（米）；
        brand_radius   —— 商场内品牌核对半径（米）。

    输出：JSON，包含
        origin        —— 定位结果（formatted_address / location）；
        searched      —— 实际检查的候选商场数量；
        matched       —— 满足全部品牌要求的商场（按距离升序）；
        partial       —— 只命中部分品牌的商场；
        unmatched     —— 一家都没命中的商场（仅列名字，便于解释）；
        note          —— 结果为空时的说明。

    限制：距离与门店均来自高德接口，禁止编造；若 matched 与 partial 都为空，
          应在 note 基础上向用户说明并建议放宽半径或更换关键词。
    """
    try:
        origin = _geocode(origin_address, city)
    except AmapError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    origin_loc = origin["location"]
    brand_list = [b.strip() for b in (brands or []) if str(b).strip()]

    try:
        malls = _around(origin_loc, "商场", mall_radius, MALL_TYPES)
    except AmapError as exc:
        return json.dumps({"error": str(exc)}, ensure_ascii=False)

    if not malls:
        try:
            malls = _around(origin_loc, "购物中心", mall_radius)
        except AmapError as exc:
            return json.dumps({"error": str(exc)}, ensure_ascii=False)

    # 限制核对次数，避免接口调用过多
    malls = malls[:10]

    matched: list[dict[str, Any]] = []
    partial: list[dict[str, Any]] = []
    unmatched: list[str] = []

    for mall in malls:
        mall_loc = mall["location"]
        hit_brands: dict[str, list[dict[str, Any]]] = {}
        miss_brands: list[str] = []

        for brand in brand_list:
            try:
                pois = _around(mall_loc, brand, brand_radius)
            except AmapError:
                pois = []
            if pois:
                hit_brands[brand] = [
                    {
                        "name": p["name"],
                        "address": p["address"],
                        "distance_in_mall_m": p["distance_m"],
                        "tel": p["tel"],
                    }
                    for p in pois[:3]
                ]
            else:
                miss_brands.append(brand)

        # 商场到用户的距离：以商场自身 distance 字段为准，缺失时单独算一次
        user_distance = mall["distance_m"]
        if user_distance == float("inf"):
            try:
                data = _amap_get(
                    "/distance",
                    {"origins": origin_loc, "destination": mall_loc, "type": 1},
                )
                results = data.get("results") or []
                user_distance = _meters(results[0].get("distance")) if results else float("inf")
            except AmapError:
                user_distance = float("inf")

        record = {
            "mall": mall["name"],
            "address": mall["address"],
            "location": mall_loc,
            "distance_m": None if user_distance == float("inf") else round(user_distance),
            "distance_text": _human_distance(user_distance),
            "brands_found": hit_brands,
            "brands_missing": miss_brands,
        }

        if brand_list and not miss_brands:
            matched.append(record)
        elif hit_brands:
            partial.append(record)
        else:
            unmatched.append(mall["name"])

    matched.sort(key=lambda r: r["distance_m"] if r["distance_m"] is not None else 10**9)
    partial.sort(
        key=lambda r: (-len(r["brands_found"]), r["distance_m"] if r["distance_m"] is not None else 10**9)
    )

    result = {
        "origin": origin,
        "brands_requested": brand_list,
        "mall_radius_m": mall_radius,
        "brand_radius_m": brand_radius,
        "searched": len(malls),
        "matched": matched,
        "partial": partial[:5],
        "unmatched": unmatched,
    }
    if not matched:
        result["note"] = (
            f"在 {mall_radius} 米内没有找到同时具备 {'、'.join(brand_list) or '全部条件'} 的商场。"
            "可建议用户放宽半径、减少品牌要求，或更换品牌关键词。"
        )
    return json.dumps(result, ensure_ascii=False)
