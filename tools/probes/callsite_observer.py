"""Reviewed source handlers: preserve predicate evaluation and original call syntax."""
SWF = 'game/fighter/didala.swf'
PATH = 'DefineSprite_542/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'
HANDLERS = {
    ('game/fighter/yulong.swf',
     'DefineSprite_345/frame_1/PlaceObject2_14_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/yijiao.swf',
     'DefineSprite_455/frame_1/PlaceObject2_18_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/ichigo.swf',
     'DefineSprite_274/frame_1/PlaceObject2_12_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/rukia.swf',
     'DefineSprite_533/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/Sasuke.swf',
     'DefineSprite_603/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/pain.swf',
     'DefineSprite_573/frame_1/PlaceObject2_18_33/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/rifagu.swf',
     'DefineSprite_638/frame_1/PlaceObject2_14_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/orochimaru.swf',
     'DefineSprite_541/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/minren.swf',
     'DefineSprite_764/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/jiraiya.swf',
     'DefineSprite_342/frame_1/PlaceObject2_11_33/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/lanran.swf',
     'DefineSprite_640/frame_1/PlaceObject2_15_33/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/Kakashi.swf',
     'DefineSprite_710/frame_1/PlaceObject2_9_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/itachi.swf',
     'DefineSprite_294/frame_1/PlaceObject2_11_33/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/gaara.swf',
     'DefineSprite_673/frame_1/PlaceObject2_20_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/daitu.swf',
     'DefineSprite_458/frame_1/PlaceObject2_21_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/Byakuya.swf',
     'DefineSprite_631/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/konan.swf',
     'DefineSprite_563/frame_1/PlaceObject2_16_32/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/juggo.swf',
     'DefineSprite_517/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/jianba.swf',
     'DefineSprite_514/frame_1/PlaceObject2_13_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/yin.swf',
     'DefineSprite_435/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/Sakura.swf',
     'DefineSprite_630/frame_1/PlaceObject2_11_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/neji.swf',
     'DefineSprite_535/frame_1/PlaceObject2_20_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/lee.swf',
     'DefineSprite_518/frame_1/PlaceObject2_18_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    ('game/fighter/Renji.swf',
     'DefineSprite_717/frame_1/PlaceObject2_16_29/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
    (SWF, PATH),
    ('game/fighter/chad.swf',
     'DefineSprite_607/frame_1/PlaceObject2_16_31/CLIPACTIONRECORD onClipEvent(enterFrame).as'),
}
SOURCE = 'onClipEvent(enterFrame){\n   if(gameRunning())\n   {\n      doAllAction();\n   }\n}\n'


def selected(record):
    return (record['swf'], record['path']) in HANDLERS


def specification(records):
    matches = [r for r in records if selected(r)]
    if len(matches) != 1 or not matches[0]['instrumented']:
        raise ValueError('missing unique instrumented call-site handler')
    return {'handler_id': matches[0]['id'], 'source': matches[0],
            'predicate': {'line': 2, 'expression': 'gameRunning()'},
            'statement': {'line': 4, 'expression': 'doAllAction();'},
            'scope': 'call-site before/after and predicate branch; not callee-body ownership'}


def instrument(source, record):
    if not selected(record):
        return source
    if source.replace('\r\n', '\n') != SOURCE:
        raise ValueError('changed/unsupported selected handler: ' + record['path'])
    def event(phase):
        return '_root.aiEvent("callsite", "' + record['id'] + ',' + phase + '," + escape(String(this)));'
    # Evaluate the original condition once. Keep the original unqualified call
    # and its receiver lookup; the false arm contains observations only.
    return ('onClipEvent(enterFrame){\n' + event('predicate_before') + '\n'
            '   if(gameRunning())\n   {\n' + event('true') + '\n' + event('call_before') + '\n'
            '      doAllAction();\n' + event('call_after') + '\n   }\n   else\n   {\n'
            + event('false') + '\n   }\n' + event('end') + '\n}\n')
