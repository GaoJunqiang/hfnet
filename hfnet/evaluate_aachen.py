import logging
from pathlib import Path
import argparse
from pprint import pformat
import yaml

# import hfnet
from hfnet.evaluation.localization import Localization, evaluate
from hfnet.evaluation.loaders import export_loader
from hfnet.settings import EXPER_PATH


configs_global = {
    'netvlad': {
        'db_name': 'globaldb_netvlad.pkl',
        'experiment': 'netvlad/aachen',
        'predictor': export_loader,
        'has_keypoints': False,
        'has_descriptors': False,
        'pca_dim': 1024,
        'num_prior': 10,
    },
}

configs_local = {
    'superpoint': {
        'db_name': 'localdb_sp-nms8.pkl',
        'experiment': 'super_point_pytorch/aachen_resize-960',
        'predictor': export_loader,
        'has_keypoints': True,
        'has_descriptors': True,
        'binarize': False,
        'do_nms': True,
        'nms_thresh': 8,
        'num_features': 1000,
        'ratio_thresh': 0.8,
    },
    'sift': {
        'db_name': 'localdb_sift.pkl',
        'colmap_db': 'aachen.db',
        'ratio_thresh': 0.7,
    },
    'doap': {
        'db_name': 'localdb_doap_kpts-sp-nms4.pkl',
        'experiment': 'doap/aachen_resize-960',
        'predictor': export_loader,
        'keypoint_predictor': export_loader,
        'keypoint_config': {
            'experiment': 'super_point_pytorch/aachen_resize-960',
            'do_nms': True,
            'nms_thresh': 4,
        },
        'num_features': 1000,
        'do_ratio_test': True,
        'ratio_thresh': 0.9,
    }
}

config_pose = {
    'reproj_error': 20,
    'min_inliers': 15,
    'min_inlier_ratio': 0.15,
}

config_aachen = {
    'resize_max': 960,
}


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('model', type=str)
    parser.add_argument('eval_name', type=str)
    parser.add_argument('--local_method', type=str)
    parser.add_argument('--global_method', type=str)
    parser.add_argument('--build_db', action='store_true')
    parser.add_argument('--queries', type=str, default='day_time')
    parser.add_argument('--max_iter', type=int)
    args = parser.parse_args()

    config = {
        'global': configs_global.get(
            args.global_method, list(configs_global.values())[0]),
        'local': configs_local.get(
            args.local_method, list(configs_local.values())[0]),
        'aachen': config_aachen,
        'pose': config_pose,
        'model': args.model,
        'max_iter': args.max_iter,
        'queries': args.queries,
    }
    logging.info(f'Configuration: \n'+pformat(config))

    logging.info('Evaluating Aachen with configuration: ')
    loc = Localization('aachen', args.model, config, build_db=args.build_db)

    query_file = f'{args.queries}_queries_with_intrinsics.txt'
    queries, query_dataset = loc.init_queries(query_file, config_aachen)

    logging.info('Starting evaluation')
    results = evaluate(loc, queries, query_dataset, max_iter=args.max_iter)
    logging.info('Evaluation results: \n'+pformat(results))

    output = {'config': config, 'results': results}
    output_path = Path(EXPER_PATH, f'eval/{args.eval_name}.yaml')
    with open(output_path, 'w') as f:
        yaml.dump(output, f, default_flow_style=False)
