"""Read-only AS2 hooks for tracing real fighter hit/guard callbacks."""

from __future__ import annotations

import re


def instrument_hit_receive(source: str, origin: str) -> str:
    """Add low-volume events around active *atm tests and receiver decisions.

    The hook evaluates each existing hitTest exactly once and records its result.
    It does not change the returned hit packet or any source field.
    """
    if not re.match(r"fighter/(?!fz/)[^#]+#", origin):
        return source

    get_hit_start = source.find("function getHitObj(")
    stage_hit_start = source.find("function getStgHitObj(", get_hit_start)
    if get_hit_start < 0 or stage_hit_start < 0:
        return source
    get_hit = source[get_hit_start:stage_hit_start]
    needle = "if(this.hitTest(_loc4_))"
    if get_hit.count(needle) != 1:
        raise ValueError(f"Expected one fighter getHitObj hitTest in {origin}")
    replacement = r'''var __hitProbe = this.hitTest(_loc4_);
         var __receiverBounds = this.getBounds(_root.game);
         var __attackBounds = _loc4_.getBounds(_root.game);
         var __bodyClip = player.bdmn == undefined ? null : player.bdmn;
         var __bodyBounds = __bodyClip == null ? null : __bodyClip.getBounds(_root.game);
         var __bodyMatrix = __bodyClip == null ? null : __bodyClip.transform.matrix;
         var __receiverMatrix = this.transform.matrix;
         var __attackMatrix = _loc4_.transform.matrix;
         var __bodyRecord = __bodyClip == null ? "undefined,undefined,undefined,undefined,undefined,undefined,undefined,undefined,undefined,undefined,undefined,undefined,undefined" : String(__bodyClip) + "," + __bodyClip._currentframe + "," + __bodyClip.getDepth() + "," + _root.aiNumber(__bodyMatrix.a) + "," + _root.aiNumber(__bodyMatrix.b) + "," + _root.aiNumber(__bodyMatrix.c) + "," + _root.aiNumber(__bodyMatrix.d) + "," + _root.aiNumber(__bodyMatrix.tx) + "," + _root.aiNumber(__bodyMatrix.ty) + "," + _root.aiNumber(__bodyBounds.xMin) + "," + _root.aiNumber(__bodyBounds.yMin) + "," + _root.aiNumber(__bodyBounds.xMax) + "," + _root.aiNumber(__bodyBounds.yMax);
         _root.aiEvent("source_hit_test", String(this) + "," + this._currentframe + "," + this.getDepth() + "," + _root.aiNumber(this.动作) + "," + _root.aiNumber(this._x) + "," + _root.aiNumber(this._y) + "," + _root.aiNumber(this._xscale) + "," + _root.aiNumber(this._yscale) + "," + _root.aiNumber(this._rotation) + "," + _root.aiNumber(__receiverMatrix.a) + "," + _root.aiNumber(__receiverMatrix.b) + "," + _root.aiNumber(__receiverMatrix.c) + "," + _root.aiNumber(__receiverMatrix.d) + "," + _root.aiNumber(__receiverMatrix.tx) + "," + _root.aiNumber(__receiverMatrix.ty) + "," + _root.aiNumber(__receiverBounds.xMin) + "," + _root.aiNumber(__receiverBounds.yMin) + "," + _root.aiNumber(__receiverBounds.xMax) + "," + _root.aiNumber(__receiverBounds.yMax) + "," + __bodyRecord + "," + String(player) + "," + _loc2_ + "," + String(_loc4_) + "," + _loc4_._currentframe + "," + _loc4_.getDepth() + "," + String(_loc4_._parent) + "," + _loc4_._parent._currentframe + "," + _root.aiNumber(_loc4_._x) + "," + _root.aiNumber(_loc4_._y) + "," + _root.aiNumber(_loc4_._xscale) + "," + _root.aiNumber(_loc4_._yscale) + "," + _root.aiNumber(_loc4_._rotation) + "," + _root.aiNumber(__attackMatrix.a) + "," + _root.aiNumber(__attackMatrix.b) + "," + _root.aiNumber(__attackMatrix.c) + "," + _root.aiNumber(__attackMatrix.d) + "," + _root.aiNumber(__attackMatrix.tx) + "," + _root.aiNumber(__attackMatrix.ty) + "," + _root.aiNumber(__attackBounds.xMin) + "," + _root.aiNumber(__attackBounds.yMin) + "," + _root.aiNumber(__attackBounds.xMax) + "," + _root.aiNumber(__attackBounds.yMax) + "," + _root.aiNumber(ppw[_loc2_ + "pw"]) + "," + _root.aiNumber(ppw[_loc2_ + "zl"]) + "," + _root.aiNumber(ppw[_loc2_ + "up"]) + "," + _root.aiNumber(ppw[_loc2_ + "x"]) + "," + _root.aiNumber(ppw[_loc2_ + "tm"]) + "," + String(ppw[_loc2_ + "dz"]) + "," + __hitProbe);
         if(__hitProbe)'''
    get_hit = get_hit.replace(needle, replacement, 1)
    source = source[:get_hit_start] + get_hit + source[stage_hit_start:]

    # Record only successful source receiver packets. The branch expression is
    # observed verbatim; the original code below still makes the decision.
    for function_name, event_name in (("fangyu", "source_guard_packet"), ("beida", "source_hit_packet")):
        pattern = re.compile(
            rf"(function {function_name}\([^)]*\)\s*\{{\s*var _loc2_ = checkHit\(\);\s*if\(!_loc2_\)\s*\{{\s*return undefined;\s*\}})",
            re.S,
        )
        matches = list(pattern.finditer(source))
        if len(matches) != 1:
            raise ValueError(f"Expected one {function_name} packet site in {origin}, got {len(matches)}")
        hook = (
            '\n   _root.aiEvent("' + event_name + '", String(this) + "," + this._currentframe + "," + '
            '_root.aiNumber(_parent._x) + "," + _root.aiNumber(_parent._y) + "," + '
            '_root.aiNumber(_parent._xscale) + "," + _root.aiNumber(_loc2_.pw) + "," + '
            '_root.aiNumber(_loc2_.zl) + "," + String(_loc2_.htype) + "," + '
            '(_loc2_.zl > 10 ? "break" : "blocked"));'
        )
        source = pattern.sub(lambda m: m.group(1) + hook, source, count=1)
    return source


def observer_schema() -> dict[str, list[str]]:
    return {
        "source_hit_test": [
            "receiver_instance", "receiver_frame", "receiver_depth", "receiver_action", "receiver_x", "receiver_y",
            "receiver_xscale", "receiver_yscale", "receiver_rotation", "receiver_matrix_a", "receiver_matrix_b",
            "receiver_matrix_c", "receiver_matrix_d", "receiver_matrix_tx", "receiver_matrix_ty",
            "receiver_bounds_xmin", "receiver_bounds_ymin", "receiver_bounds_xmax", "receiver_bounds_ymax",
            "target_bdmn_instance", "target_bdmn_frame", "target_bdmn_depth", "target_bdmn_matrix_a",
            "target_bdmn_matrix_b", "target_bdmn_matrix_c", "target_bdmn_matrix_d", "target_bdmn_matrix_tx",
            "target_bdmn_matrix_ty", "target_bdmn_bounds_xmin", "target_bdmn_bounds_ymin",
            "target_bdmn_bounds_xmax", "target_bdmn_bounds_ymax", "target_clip", "hit_key",
            "attack_instance", "attack_frame", "attack_depth", "attack_parent", "attack_parent_frame",
            "attack_x", "attack_y", "attack_xscale", "attack_yscale", "attack_rotation",
            "attack_matrix_a", "attack_matrix_b", "attack_matrix_c", "attack_matrix_d",
            "attack_matrix_tx", "attack_matrix_ty", "attack_bounds_xmin", "attack_bounds_ymin",
            "attack_bounds_xmax", "attack_bounds_ymax", "pw", "zl", "up", "x", "tm", "dz",
            "hit_test_result",
        ],
        "source_guard_packet": [
            "receiver_instance", "receiver_frame", "receiver_x", "receiver_y", "receiver_facing",
            "pw", "zl", "htype", "source_branch_zl_gt_10",
        ],
        "source_hit_packet": [
            "receiver_instance", "receiver_frame", "receiver_x", "receiver_y", "receiver_facing",
            "pw", "zl", "htype", "source_branch_zl_gt_10",
        ],
    }
