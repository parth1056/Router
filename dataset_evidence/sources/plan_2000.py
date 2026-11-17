"""Build the approved 2,000 train / 200 dev / 300 test plan.

Reuses the supplied TRAIN-ONLY starting material (seed100 + pair recipe bank + state recipes) and
extends the allocation to the approved sizes. Code owns states, roles, operative offers and the
neutral current message; the model writes user utterances only. Evaluation scenarios, wording and
families are entirely separate from training.
"""
import collections
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
PACK = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PACK / 'reference'))
from state_recipes import make_state  # noqa: E402

OUT = PACK / 'data/corpus2'
SEED = PACK / 'seed/seed100_ai_reviewed_candidates.jsonl'
BANK = PACK / 'seed/pair_recipe_bank.json'

# Scenario settings, split-exclusive, so families and siblings never cross a split.
TRAIN_SCENES = [
    'graduation portrait', 'volunteer event photo', 'local theatre poster', 'picnic group photo',
    'visitor badge photo', 'handwritten note', 'employee profile portrait', 'archived family portrait',
    'concert backstage photo', 'sports team portrait', 'restored family photograph',
    'student club announcement', 'artist portfolio portrait', 'community newsletter photo',
    'conference speaker portrait', 'photography class portrait', 'library exhibition photo',
    'photographed text message', 'charity campaign portrait', 'museum visitor photo',
    'bakery storefront photo', 'hiking trail snapshot', 'wedding reception photo',
    'warehouse loading bay photo', 'cooking class photo', 'train station platform photo',
    'garden centre plant label', 'school science fair poster', 'band rehearsal photo',
    'hotel lobby photo', 'football match photo', 'village hall notice', 'childhood birthday photo',
    'post office queue photo', 'roof repair photo', 'music lesson photo', 'farm tractor photo',
    'swimming lesson photo', 'book club photo', 'church fete photo', 'car boot sale photo',
    'dentist waiting room photo', 'rock pooling photo', 'sunday market photo', 'bus timetable photo',
    'office party photo', 'allotment shed photo', 'soft play centre photo', 'holiday coach photo',
    'athletics meeting photo', 'piano recital photo', 'nursery classroom photo', 'beach clean photo',
    'camping trip photo', 'fireworks night photo', 'kitchen renovation photo', 'recycling point photo',
    'toy shop window photo', 'cycle path photo', 'pond dipping photo', 'school play photo',
    'sports day photo', 'museum workshop photo', 'hotel breakfast photo', 'laundry room photo',
    'harbour wall photo', 'falconry display photo', 'clothes swap photo', 'tree planting photo',
    'quiz night photo', 'knitting group photo', 'bakery counter photo', 'bus depot photo',
    'nature reserve photo', 'town hall photo', 'sports club dinner photo', 'summer fair photo',
    'care home visit photo', 'gardening club photo', 'beach hut photo', 'pier photo',
    'woodland walk photo', 'castle visit photo', 'market stall photo', 'library reading room photo',
    'pool league photo', 'bowling alley photo', 'ice rink photo', 'skate park photo',
    'golf course photo', 'rugby club photo', 'cricket match photo', 'rowing club photo',
    'art class photo', 'pottery kiln photo', 'bike repair photo', 'farm shop photo',
    'science museum photo', 'aquarium photo', 'zoo enclosure photo', 'planetarium photo',
    'florist shop photo', 'deli counter photo', 'farmers coop photo', 'printing workshop photo',
    'recording studio photo', 'dance class photo', 'gym session photo', 'martial arts class photo',
    'chess tournament photo', 'debating society photo', 'student newspaper photo', 'debate final photo',
    'open day photo', 'graduation ceremony photo', 'prize giving photo', 'charity run photo',
    'clinic open day photo', 'community fridge photo', 'repair workshop photo', 'seed swap photo',
]
DEV_SCENES = [
    'ferry ticket photo', 'pottery workshop portrait', 'street food stall photo',
    'veterinary clinic poster', 'rooftop garden photo', 'chess club portrait',
    'museum ticket stub', 'cycling club photo', 'harbour ferry queue', 'puppet show photo',
    'angling club photo', 'soup kitchen photo', 'library book sale photo', 'ceilidh dance photo',
    'snow day photo', 'beekeeping photo', 'model railway photo', 'brass band photo',
    'dog training photo', 'wildflower meadow photo', 'local radio studio photo', 'cricket nets photo',
    'scout hut photo', 'jumble sale photo', 'church bell tower photo', 'canal boat photo',
    'stone circle photo', 'orchid greenhouse photo', 'wood turning photo', 'lifeboat station photo',
]
TEST_SCENES = [
    'farmers market photo', 'choir performance portrait', 'mountain rescue team photo',
    'community kitchen photo', 'bookshop window photo', 'swimming gala portrait',
    'repair cafe photo', 'holiday cottage interior', 'orchestra rehearsal photo',
    'allotment garden photo', 'village fete poster', 'birdwatching photo',
    'drama rehearsal portrait', 'food bank parcel photo', 'windmill photo', 'tram stop photo',
    'archive reading room photo', 'coastal path photo', 'school library photo', 'pottery fair photo',
    'community orchard photo', 'lamplight procession photo', 'boxing club photo', 'bake off photo',
    'salvation army band photo', 'botanical glasshouse photo', 'market cross photo',
    'fishing harbour photo', 'rowing regatta photo', 'heritage railway photo', 'castle grounds photo',
    'cider press photo', 'knitting circle photo', 'market research stand photo', 'lighthouse photo',
    'mining museum photo', 'coracle race photo', 'town crier photo', 'apple day photo',
    'wetland boardwalk photo', 'garden railway photo', 'sheepdog trial photo', 'carnival float photo',
    'beekeepers market photo', 'pier fireworks photo', 'chapel choir photo', 'village green photo',
    'ferry terminal photo', 'bus rally photo', 'chalk stream photo',
]

# Split-specific wording banks (no overlap between splits).
WORDING = {
    'train': {
        'continuations': {'NEW_TARGET_CONTINUATION': ['And this one?'],
                          'REPEAT_PREVIOUS_OPERATION': ['Check it again, please.'],
                          'ACCEPT_CLEAR_OFFER': ['Yes, please do that.', 'Go ahead with that.']},
        'frames': ['I can {action}. Would you like me to?', 'Would you like me to {action}?'],
        'base_action': 'explain the stored result',
        'deepfake_action': 'run a fresh authenticity check on it',
        'repeat_base': 'I read the text in the image again: it is unchanged.',
        'repeat_deepfake': 'I ran the authenticity check again; the recorded verdict is {verdict}.',
        'new_base': 'I described the first image: people are standing together in daylight.',
        'new_deepfake': 'I checked the first image earlier; the recorded verdict is {verdict}.',
    },
    'dev': {
        'continuations': {'NEW_TARGET_CONTINUATION': ['What about this next one?'],
                          'REPEAT_PREVIOUS_OPERATION': ['Could you repeat that, please?'],
                          'ACCEPT_CLEAR_OFFER': ['Yes, go ahead.']},
        'frames': ['Shall I {action}?', 'I could {action} for you. Should I?'],
        'base_action': 'walk through the stored result',
        'deepfake_action': 'run a new authenticity check',
        'repeat_base': 'Here is the text from the image once more: unchanged.',
        'repeat_deepfake': 'Second authenticity run complete; the verdict is {verdict}.',
        'new_base': 'First image description: a group gathered indoors in bright light.',
        'new_deepfake': 'First image result, as recorded: {verdict}.',
    },
    'test': {
        'continuations': {'NEW_TARGET_CONTINUATION': ['Now this one too.'],
                          'REPEAT_PREVIOUS_OPERATION': ['Do that once more.'],
                          'ACCEPT_CLEAR_OFFER': ['Please do that.']},
        'frames': ['Would it help if I {action}?', 'I am able to {action}. Do you want that?'],
        'base_action': 'summarise the existing result',
        'deepfake_action': 'carry out another authenticity check',
        'repeat_base': 'The image text has been read again and has not changed.',
        'repeat_deepfake': 'The check was repeated; the recorded verdict is {verdict}.',
        'new_base': 'I have described the first image: people posing together outdoors.',
        'new_deepfake': 'The first image was checked and recorded as {verdict}.',
    },
}

SINGLE_RECIPES = {
    'general_chat': ('BASE', 'no_assets',
                     'Write one short ordinary request in this scenario that needs no image: wording, '
                     'planning or an everyday explanation. No authenticity checking.'),
    'ordinary_image': ('BASE', 'ready',
                       'Write one short request about appearance, content or a caption of the attached '
                       'image. Do not ask about authenticity or manipulation.'),
    'conceptual_authenticity': ('BASE', 'ready',
                                'Write one short conceptual question about deepfakes, synthetic media or '
                                'detectors. Do not ask to check the attached image.'),
    'negation_quotes_injection': ('BASE', 'ready',
                                  'Write one short request that mentions a detector, a quoted command or a '
                                  'quoted phrase but whose actual task is translate/read/explain/describe.'),
    'explain_existing': ('BASE', 'stored_alt',
                         'Write one short request to explain or summarise the EXISTING stored verdict '
                         'in plain language. Do not ask for a new check.'),
    'clarify_or_unsupported': ('BASE', 'restricted',
                               'Write one short request asking for a real/fake check on the image the '
                               'user thinks is attached. Do not mention metadata or availability.'),
    'explicit_authenticity': ('DEEPFAKE', 'ready',
                              'Write one short direct request for a NEW real/fake or AI-generated verdict '
                              'on the attached image.'),
    'indirect_authenticity': ('DEEPFAKE', 'ready',
                              'Write one short request where the user sounds suspicious about the attached '
                              'image and wants it verified, without saying "deepfake" or "real or fake".'),
    'explicit_reanalysis': ('DEEPFAKE', 'stored_alt',
                            'Write one short request to run the authenticity check AGAIN on the same '
                            'image, rather than explaining the old result.'),
    'new_image_or_mixed': ('DEEPFAKE', 'new_alt',
                           'Write one short request for a verdict on the newly selected image, optionally '
                           'combined with a caption or reading task.'),
}

RESTRICTED = ['no_assets', 'missing', 'expired', 'unsupported', 'unknown', 'multiple', 'video']

PAIR_KINDS = [
    ('NEW_TARGET_CONTINUATION', 'new', 'ordinary_image', 'new_image_or_mixed',
     'Write the ONE earlier user request that led the assistant to look at the first image in an '
     'ordinary way. Do not write the assistant reply.',
     'Write the ONE earlier user request that led the assistant to check the first image for '
     'authenticity. Do not write the assistant reply.'),
    ('REPEAT_PREVIOUS_OPERATION', 'stored_alt', 'ordinary_image', 'explicit_reanalysis',
     'Write the ONE earlier user request that led the assistant to read the text in the image. Do '
     'not write the assistant reply.',
     'Write the ONE earlier user request that led the assistant to run an authenticity check. Do '
     'not write the assistant reply.'),
    ('ACCEPT_CLEAR_OFFER', 'stored_alt', 'explain_existing', 'explicit_reanalysis',
     'Write the ONE earlier user request that made the assistant offer to explain the stored '
     'result. Do not write the assistant reply.',
     'Write the ONE earlier user request that made the assistant offer a fresh authenticity check. '
     'Do not write the assistant reply.'),
]


def seed_rows():
    return [json.loads(line) for line in SEED.read_text(encoding='utf-8').splitlines() if line.strip()]


def bank():
    return json.loads(BANK.read_text(encoding='utf-8'))


def state_for(recipe, index):
    name = recipe
    if name == 'stored_alt':
        name = 'stored_fake' if index % 2 else 'stored_real'
    elif name == 'new_alt':
        name = 'new' if index % 2 else 'new_old_missing'
    elif name == 'restricted':
        name = RESTRICTED[index % len(RESTRICTED)]
    return make_state(name)


def verdict_of(state):
    return 'REAL' if (state['last_analysis'] or {}).get('verdict') == 'REAL' else 'FAKE'


def pair_family(split, family_id, scene, kind, surface, index):
    lineage, recipe, base_cat, deep_cat, base_brief, deep_brief = kind
    w = WORDING[split]
    state = state_for(recipe, index)
    verdict = verdict_of(state)
    conts = w['continuations'][lineage]
    message = conts[surface % len(conts)]
    if lineage == 'NEW_TARGET_CONTINUATION':
        base_reply = w['new_base']
        deep_reply = w['new_deepfake'].format(verdict=verdict)
    elif lineage == 'REPEAT_PREVIOUS_OPERATION':
        base_reply = w['repeat_base']
        deep_reply = w['repeat_deepfake'].format(verdict=verdict)
    else:
        frame = w['frames'][surface % len(w['frames'])]
        base_reply = frame.format(action=w['base_action'])
        deep_reply = frame.format(action=w['deepfake_action'])
    return {
        'job_id': family_id + '_pair', 'family_id': family_id, 'split': split, 'scene': scene,
        'mode': 'context_pair', 'recipe_group': lineage,
        'fixed_current_message': message,
        'runtime_state': state,
        'variants': [
            {'slot_id': family_id + '_b', 'category': base_cat, 'intended_route': 'BASE',
             'request_brief': base_brief, 'assistant_reply': base_reply},
            {'slot_id': family_id + '_d', 'category': deep_cat, 'intended_route': 'DEEPFAKE',
             'request_brief': deep_brief, 'assistant_reply': deep_reply},
        ]}


def single_family(split, family_id, scene, category, count, index):
    route, recipe, brief = SINGLE_RECIPES[category]
    state = state_for(recipe, index)
    slots = [{'slot_id': '%s_%d' % (family_id, v + 1), 'category': category,
              'intended_route': route, 'request_brief': brief, 'runtime_state': state}
             for v in range(count)]
    return {'job_id': family_id + '_single', 'family_id': family_id, 'split': split, 'scene': scene,
            'mode': 'single', 'recipe_group': 'SINGLE_' + category,
            'fixed_current_message': None, 'variants': slots}


TRAIN_SINGLE_QUOTA = {
    'general_chat': 30, 'ordinary_image': 30, 'conceptual_authenticity': 25,
    'negation_quotes_injection': 25, 'clarify_or_unsupported': 20, 'explain_existing': 15,
    'explicit_authenticity': 35, 'indirect_authenticity': 35, 'explicit_reanalysis': 20,
    'new_image_or_mixed': 15,
}
DEV_SINGLE_QUOTA = {'general_chat': 4, 'ordinary_image': 4, 'conceptual_authenticity': 3,
                    'negation_quotes_injection': 3, 'clarify_or_unsupported': 3,
                    'explain_existing': 3, 'explicit_authenticity': 5, 'indirect_authenticity': 3,
                    'explicit_reanalysis': 1, 'new_image_or_mixed': 1}
TEST_SINGLE_QUOTA = {'general_chat': 6, 'ordinary_image': 6, 'conceptual_authenticity': 4,
                     'negation_quotes_injection': 4, 'clarify_or_unsupported': 5,
                     'explain_existing': 5, 'explicit_authenticity': 8, 'indirect_authenticity': 4,
                     'explicit_reanalysis': 2, 'new_image_or_mixed': 1}


def build_split(split, scenes, single_quota, pair_count, seed_ext=None):
    jobs = []
    fam = 0
    if seed_ext:
        for job in seed_ext:
            jobs.append(job)
    # new pair families, cycling the three reviewed recipe kinds and the scenario list
    for i in range(pair_count):
        kind = PAIR_KINDS[i % len(PAIR_KINDS)]
        fam += 1
        family_id = 'fam2_%s_p%03d' % (split, fam)
        jobs.append(pair_family(split, family_id, scenes[i % len(scenes)], kind, i // len(PAIR_KINDS),
                                i))
    # new single families
    idx = 0
    for category, count in single_quota.items():
        for _ in range(count):
            fam += 1
            family_id = 'fam2_%s_s%03d' % (split, fam)
            jobs.append(single_family(split, family_id, scenes[idx % len(scenes)], category, 4, idx))
            idx += 1
    return jobs


def seed_extensions(rows):
    """Extend each seed family inside TRAIN_ONLY: +2 pair rows, +3 paraphrases per single row."""
    bank_recipes = {r['family_id']: r for r in bank()}
    jobs = []
    by_family = collections.defaultdict(list)
    for r in rows:
        by_family[r['family_id']].append(r)
    for family_id, members in sorted(by_family.items()):
        if len(members) == 2:
            recipe = bank_recipes[family_id]
            w = WORDING['train']
            state = members[0]['input']
            jobs.append({
                'job_id': family_id + '_ext_pair', 'family_id': family_id, 'split': 'train',
                'scene': recipe['scenario'], 'mode': 'context_pair', 'recipe_group': 'SEED_EXTENSION',
                'fixed_current_message': [c for c in
                                          WORDING['train']['continuations'][recipe['template_lineage']]
                                          if c != recipe['current_message']][0]
                if len(WORDING['train']['continuations'][recipe['template_lineage']]) > 1 else
                WORDING['train']['continuations'][recipe['template_lineage']][0],
                'runtime_state': {'assets': state['assets'],
                                  'active_image_id': state['active_image_id'],
                                  'last_analysis': state['last_analysis']},
                'variants': [
                    {'slot_id': family_id + '_ext_b', 'category': recipe['base_category'],
                     'intended_route': 'BASE',
                     'request_brief': 'Write the ONE earlier user request for this reviewed family, '
                                      'variant 2. The assistant reply is code-owned.',
                     'assistant_reply': recipe['base_assistant'].format(
                         scene=recipe['scenario'],
                         verdict=(state['last_analysis'] or {}).get('verdict', 'recorded'))},
                    {'slot_id': family_id + '_ext_d', 'category': recipe['deepfake_category'],
                     'intended_route': 'DEEPFAKE',
                     'request_brief': 'Write the ONE earlier user request for this reviewed family, '
                                      'variant 2. The assistant reply is code-owned.',
                     'assistant_reply': recipe['deepfake_assistant'].format(
                         scene=recipe['scenario'],
                         verdict=(state['last_analysis'] or {}).get('verdict', 'recorded'))},
                ]})
        else:
            row = members[0]
            state = row['input']
            slots = [{'slot_id': '%s_para%d' % (family_id, v + 1), 'category': row['category'],
                      'intended_route': row['label'],
                      'request_brief': 'Paraphrase this reviewed request naturally, keeping the same '
                                       'task and state: "%s"' % row['input']['message'],
                      'runtime_state': {'assets': state['assets'],
                                        'active_image_id': state['active_image_id'],
                                        'last_analysis': state['last_analysis']}}
                     for v in range(3)]
            jobs.append({'job_id': family_id + '_ext_single', 'family_id': family_id, 'split': 'train',
                         'scene': row['scenario'], 'mode': 'single', 'recipe_group': 'SEED_PARAPHRASE',
                         'fixed_current_message': None, 'variants': slots})
    return jobs


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    rows = seed_rows()
    ext = seed_extensions(rows)
    plans = {
        'train': build_split('train', TRAIN_SCENES, TRAIN_SINGLE_QUOTA, 340, seed_ext=ext),
        'dev': build_split('dev', DEV_SCENES, DEV_SINGLE_QUOTA, 40),
        'test': build_split('test', TEST_SCENES, TEST_SINGLE_QUOTA, 60),
    }
    summary = {}
    for split, jobs in plans.items():
        slots = [v for j in jobs for v in j['variants']]
        fams = {j['family_id'] for j in jobs}
        routes = collections.Counter(v['intended_route'] for v in slots)
        sizes = {f: sum(len(j['variants']) for j in jobs if j['family_id'] == f) for f in fams}
        assert len({s['slot_id'] for s in slots}) == len(slots)
        seed_count = len(rows) if split == 'train' else 0
        variant_count = dict(sizes)
        if split == 'train':
            for r in rows:
                variant_count[r['family_id']] = variant_count.get(r['family_id'], 0) + 1
        assert max(variant_count.values()) <= 4, (split, max(variant_count.values()))
        summary[split] = {'generated_rows': len(slots), 'seed_rows': seed_count,
                          'rows': len(slots) + seed_count, 'families': len(fams),
                          'jobs': len(jobs), 'routes': dict(routes),
                          'context_rows': sum(2 for j in jobs if j['mode'] == 'context_pair'),
                          'max_variants_per_family': max(variant_count.values())}
        (OUT / ('%s_jobs.json' % split)).write_text(
            json.dumps(jobs, indent=1, ensure_ascii=False) + '\n', encoding='utf-8')
    # seed rows are part of train exactly once
    seed_rows_out = []
    for r in rows:
        rec = dict(r)
        rec['split'] = 'train'
        rec['provenance'] = {'source': 'seed/seed100_ai_reviewed_candidates.jsonl',
                             'label_source': r['label_source'], 'human_reviewed': False,
                             'split_reservation': 'TRAIN_ONLY'}
        seed_rows_out.append(rec)
    (OUT / 'train_seed_rows.jsonl').write_text(
        ''.join(json.dumps(r, sort_keys=True) + '\n' for r in seed_rows_out), encoding='utf-8')
    scenes = {'train': TRAIN_SCENES, 'dev': DEV_SCENES, 'test': TEST_SCENES}
    for a in scenes:
        for b in scenes:
            if a < b:
                assert not (set(scenes[a]) & set(scenes[b])), (a, b)
    expected = {'train': 2000, 'dev': 200, 'test': 300}
    for split in expected:
        assert summary[split]['rows'] == expected[split], (split, summary[split]['rows'])
    (OUT / 'PLAN_SUMMARY.json').write_text(json.dumps(summary, indent=2) + '\n', encoding='utf-8')
    (OUT / 'recipes.json').write_text(json.dumps(
        {'wording': WORDING, 'single_recipes': SINGLE_RECIPES, 'pair_kinds': [
            {'lineage': k[0], 'state_recipe': k[1], 'base_category': k[2], 'deepfake_category': k[3]}
            for k in PAIR_KINDS], 'restricted_states': RESTRICTED,
         'note': 'Code owns state, roles, offers and current messages; the model writes user '
                 'utterances only.'}, indent=2) + '\n', encoding='utf-8')
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
