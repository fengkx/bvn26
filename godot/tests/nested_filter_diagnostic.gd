extends "res://tests/nested_buffer_diagnostic.gd"
const FilterPreview = preload("res://tests/nested_filter_preview.gd")

func _filter(kind: String, amount: float, color: Array) -> Dictionary:
    if kind == "BLURFILTER":
        return {"type": kind, "blurX": amount, "blurY": amount, "passes": 1}
    return {"type": kind, "blurX": amount, "blurY": amount, "passes": 1,
        "color": color, "strength": 1.0, "innerGlow": false, "knockout": false, "compositeSource": true}

func _run() -> void:
    var args := OS.get_cmdline_user_args()
    assert(args.size() == 2)
    var fixture: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(args[0]))
    assert(fixture.production_admitted == false and fixture.cases.size() == 48)
    for spec: Dictionary in fixture.cases:
        var view := SubViewport.new()
        view.size = Vector2i(24, 24)
        view.transparent_bg = true
        view.world_2d = World2D.new()
        view.render_target_update_mode = SubViewport.UPDATE_ALWAYS
        root.add_child(view)
        var preview := FilterPreview.new()
        preview.autoplay = false
        preview.play_timeline_sounds = false
        preview.show_collision_shapes = false
        _add(preview, spec.inputs.back, Vector2i(24,24), Vector2.ZERO)
        _add(preview, spec.inputs.middle, Vector2i(16,16), Vector2(2,2))
        _add(preview, spec.inputs.leaf_a, Vector2i(8,8), Vector2(6,6))
        _add(preview, spec.inputs.leaf_b, Vector2i(4,4), Vector2(8,8))
        var mul := Color(0.5,0.75,1,1) if spec.key[5] else Color.WHITE
        var add := Color(8.0/255,0,-4.0/255,0) if spec.key[5] else Color(0,0,0,0)
        var child_filter := _filter("GLOWFILTER" if spec.key[1] == 0 else "BLURFILTER", 5, [81.0/255,211.0/255,239.0/255,1])
        var parent_filter := _filter("BLURFILTER" if spec.key[1] == 0 else "GLOWFILTER", 3, [93.0/255,225.0/255,244.0/255,1])
        preview._compose_blend_group(2, float(spec.key[3])/100, 0, 1, [child_filter], true, mul, add)
        preview._compose_blend_group(1, float(spec.key[4])/100, 0, 1, [parent_filter], true, mul, add)
        _add(preview, spec.inputs.sentinel, Vector2i(2,24), Vector2(10,0))
        assert(preview.diagnostic_groups.size() == 2)
        var child: Node2D = preview.diagnostic_groups[0]
        var parent: Node2D = preview.diagnostic_groups[1]
        assert(child.get_parent() == parent.get_node("Contents"))
        view.add_child(preview)
        views.append(view)
        groups.append([child,parent])
    for tick in 24:
        await process_frame
        await RenderingServer.frame_post_draw
    var atlases := {}
    for stage in ["child_input", "child_filter", "parent_input", "parent_filter", "final"]:
        var size := 12 if stage.begins_with("child") else (18 if stage.begins_with("parent") else 24)
        atlases[stage] = Image.create(size, size*48, false, Image.FORMAT_RGBA8)
    for i in views.size():
        var observations: Array = []
        for j in 2:
            var group: Node2D = groups[i][j]
            assert(group.get_script().resource_path == "res://filter_group.gd")
            var contents: SubViewport = group.get_node("Contents")
            var composite: Sprite2D = group.get_node("Composite")
            var size := 12 if j == 0 else 18
            var prefix := "child" if j == 0 else "parent"
            assert(contents.size == Vector2i(size,size))
            for stage in ["input", "filter"]:
                var image := contents.get_texture().get_image() if stage == "input" else composite.texture.get_image()
                assert(image.get_size() == Vector2i(size,size))
                atlases[prefix+"_"+stage].blit_rect(image, Rect2i(0,0,size,size), Vector2i(0,i*size))
            var origin: Vector2 = group.global_transform * composite.position
            var passes: Array = []
            for node in group.get_children():
                if node is SubViewport and node.name.begins_with("FilterPass"):
                    passes.append([node.size.x,node.size.y])
            observations.append({"size": [size,size], "origin": [origin.x,origin.y], "passes": passes})
        atlases.final.blit_rect(views[i].get_texture().get_image(), Rect2i(0,0,24,24), Vector2i(0,i*24))
        records.append({"case": i, "groups": observations, "production_admitted": false})
    for stage in atlases:
        assert(atlases[stage].save_png(args[1].path_join(stage+".png")) == OK)
    FileAccess.open(args[1].path_join("buffers.json"), FileAccess.WRITE).store_string(JSON.stringify(records,"\t")+"\n")
    print("NESTED_FILTER_DIAGNOSTIC_OK cases=48")
    quit(0)
