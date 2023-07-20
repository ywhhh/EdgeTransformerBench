"""
Reference code:
    https://github.com/microsoft/onnxruntime/blob/main/onnxruntime/python/tools/microbench/benchmark.py
    https://github.com/microsoft/onnxruntime-inference-examples/blob/main/python/api/onnxruntime-python-api.py
    https://onnxruntime.ai/docs/get-started/with-python.html
"""

import os
import onnxruntime as ort
import time
import numpy as np
import torch
import argparse
from speed_test import load_image
from speed_test import WARMUP_SEC, TEST_SEC
from main import build_dataset, MetricLogger
from timm.utils import accuracy

def get_args_parser():
    parser = argparse.ArgumentParser(
        'EdgeTransformerPerf onnxruntime evaluation and benchmark script', add_help=False)
    parser.add_argument('--batch-size', default=1, type=int)
    parser.set_defaults(IOBinding=True)
    parser.add_argument('--no-IOBinding', action='store_false', dest='IOBinding')
    # Dataset parameters
    parser.add_argument('--validation', action='store_true', default=False)
    parser.add_argument('--data-path', default='imagenet-div50', type=str, help='dataset path')
    parser.add_argument('--num_workers', default=2, type=int)
    # Benchmark parameters
    parser.set_defaults(cpu=True)
    parser.add_argument('--no-cpu', action='store_false', dest='cpu')
    parser.add_argument('--cuda', action='store_true', default=False)
    parser.add_argument('--only-test', default='', type=str, help='only test a certain model series')

    return parser

def numpy_type(torch_type):
    type_map = {
        torch.float32: np.float32,
        torch.float16: np.float16,
        torch.int32: np.int32,
        torch.int64: np.int64,
    }
    return type_map[torch_type]

def benchmarking_onnx(sess, image, args):
    if args.IOBinding:
        io_binding = sess.io_binding()
        inputs = torch.empty(args.batch_size, 3, args.input_size, args.input_size).to(args.device)#.contiguous() #TODO:?
        output = torch.empty(args.batch_size, 1000).to(args.device)#.contiguous()
        io_binding.bind_input(args.input_name, args.device, 0, numpy_type(inputs.dtype), inputs.shape, inputs.data_ptr())
        io_binding.bind_output(args.output_name, args.device, 0, numpy_type(output.dtype), output.shape, output.data_ptr())

        # https://discuss.pytorch.org/t/what-is-the-recommended-way-to-re-assign-update-values-in-a-variable-or-tensor/6125
        inputs.data.copy_(image.data)
    else:
        inputs = image.numpy()

    # warmup
    start = time.perf_counter()
    while time.perf_counter() - start < WARMUP_SEC:
        if args.IOBinding:
            sess.run_with_iobinding(io_binding)
        else:
            output = sess.run(None, {'input': inputs})
            output = torch.Tensor(np.array(output[0]))

    val, idx = output.topk(3)
    print(list(zip(idx[0].tolist(), val[0].tolist())))

    time_list = []
    while sum(time_list) < TEST_SEC:
        start = time.perf_counter()
        if args.IOBinding:
            sess.run_with_iobinding(io_binding)
        else:
            output = sess.run(None, {'input': inputs})

        time_list.append(time.perf_counter() - start)

    time_max = max(time_list) * 1000
    time_min = min(time_list) * 1000
    time_mean   = np.mean(time_list)   * 1000
    time_median = np.median(time_list) * 1000
    print("min = {:7.2f}ms  max = {:7.2f}ms  mean = {:7.2f}ms, median = {:7.2f}ms".format(time_min, time_max, time_mean, time_median))

def evaluate(data_loader, sess, args):
    criterion = torch.nn.CrossEntropyLoss()

    metric_logger = MetricLogger(delimiter="  ")
    header = 'Test:'

    if args.IOBinding:
        io_binding = sess.io_binding()
        inputs = torch.empty(args.batch_size, 3, args.input_size, args.input_size).to(args.device)#.contiguous() #TODO:?
        output = torch.empty(args.batch_size, 1000).to(args.device)#.contiguous()
        io_binding.bind_input(args.input_name, args.device, 0, numpy_type(inputs.dtype), inputs.shape, inputs.data_ptr())
        io_binding.bind_output(args.output_name, args.device, 0, numpy_type(output.dtype), output.shape, output.data_ptr())

    dataset_scale = 50000//args.len_dataset_val
    for images, target in metric_logger.log_every(data_loader, 50, header):
        target = target * dataset_scale + (15 if dataset_scale == 50 else 0)

        if args.IOBinding:
            inputs.data.copy_(images.data)
            target = target.to(args.device)
            sess.run_with_iobinding(io_binding)
        else:
            output = sess.run(None, {'input': images.numpy()})
            output = torch.Tensor(np.array(output[0]))

        loss = criterion(output, target)
        acc1, acc5 = accuracy(output, target, topk=(1, 5))
        metric_logger.update(loss=loss.item())

        batch_size = images.shape[0]
        metric_logger.meters['acc1'].update(acc1.item(), n=batch_size)
        metric_logger.meters['acc5'].update(acc5.item(), n=batch_size)

    # gather the stats from all processes
    metric_logger.synchronize_between_processes()
    print('* Acc@1 {top1.global_avg:.3f} Acc@5 {top5.global_avg:.3f} loss {losses.global_avg:.3f}'
          .format(top1=metric_logger.acc1, top5=metric_logger.acc5, losses=metric_logger.loss))
    print(output.mean().item(), output.std().item())

    test_stats = {k: meter.global_avg for k, meter in metric_logger.meters.items()}
    print(f"Accuracy on {args.len_dataset_val} test images: {test_stats['acc1']:.1f}%")


if __name__ == '__main__':
    parser = get_args_parser()
    args = parser.parse_args()
    device_list = []
    if args.cpu: device_list.append('cpu')
    if args.cuda: device_list.append('cuda')

    for device in device_list:
        if 'cuda' in device and not torch.cuda.is_available():
            print("no cuda")
            continue

        args.device = device

        sess_options = ort.SessionOptions()
        if device == 'cpu':
            os.system('echo -n "nb processors "; '
                    'cat /proc/cpuinfo | grep ^processor | wc -l; '
                    'cat /proc/cpuinfo | grep ^"model name" | tail -1')
            print('Using 1 cpu thread')
            providers = ['CPUExecutionProvider']
            # https://onnxruntime.ai/docs/performance/tune-performance/threading.html
            sess_options.intra_op_num_threads = 1
            # default: sess_options.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        else:
            print(torch.cuda.get_device_name(torch.cuda.current_device()))
            opt_dict = {}
            # opt_dict["cudnn_conv_use_max_workspace"] = '1'
            # https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#performance-tuning
            if args.IOBinding:
                # https://onnxruntime.ai/docs/execution-providers/CUDA-ExecutionProvider.html#using-cuda-graphs-preview
                # requires using IOBinding so as to bind memory which will be used as input(s)/output(s) for the CUDA Graph machinery to read from/write to
                # otherwise will segmentfault in evaluation
                opt_dict["enable_cuda_graph"] = '1'
            providers = [("CUDAExecutionProvider", opt_dict)]

        for name, resolution, usi_eval, weight in [
            ('efficientformerv2_s0', 224, False, "eformer_s0_450.pth"),
            ('efficientformerv2_s1', 224, False, "eformer_s1_450.pth"),
            ('efficientformerv2_s2', 224, False, "eformer_s2_450.pth"),

            ('SwiftFormer_XS', 224, False, "SwiftFormer_XS_ckpt.pth"),
            ('SwiftFormer_S' , 224, False, "SwiftFormer_S_ckpt.pth"),
            ('SwiftFormer_L1', 224, False, "SwiftFormer_L1_ckpt.pth"),

            ('EMO_1M', 224, False, "EMO_1M.pth"),
            ('EMO_2M', 224, False, "EMO_2M.pth"),
            ('EMO_5M', 224, False, "EMO_5M.pth"),
            ('EMO_6M', 224, False, "EMO_6M.pth"),

            ('edgenext_xx_small', 256, False, "edgenext_xx_small.pth"),
            ('edgenext_x_small' , 256, False, "edgenext_x_small.pth"),
            ('edgenext_small'   , 256, True, "edgenext_small_usi.pth"),

            ('mobilevitv2_050', 256, False, "mobilevitv2-0.5.pt"),
            ('mobilevitv2_075', 256, False, "mobilevitv2-0.75.pt"),
            ('mobilevitv2_100', 256, False, "mobilevitv2-1.0.pt"),
            ('mobilevitv2_125', 256, False, "mobilevitv2-1.25.pt"),
            ('mobilevitv2_150', 256, False, "mobilevitv2-1.5.pt"),
            ('mobilevitv2_175', 256, False, "mobilevitv2-1.75.pt"),
            ('mobilevitv2_200', 256, False, "mobilevitv2-2.0.pt"),

            ('mobilevit_xx_small', 256, False, "mobilevit_xxs.pt"),
            ('mobilevit_x_small' , 256, False, "mobilevit_xs.pt"),
            ('mobilevit_small'   , 256, False, "mobilevit_s.pt"),

            ('LeViT_128S', 224, False, "LeViT-128S.pth"),
            ('LeViT_128' , 224, False, "LeViT-128.pth"),
            ('LeViT_192' , 224, False, "LeViT-192.pth"),
            ('LeViT_256' , 224, False, "LeViT-256.pth"),

            ('resnet50', 224, False, ""),
            ('mobilenetv3_large_100', 224, False, ""),
            ('tf_efficientnetv2_b0' , 224, False, ""),
            ('tf_efficientnetv2_b1' , 240, False, ""),
            ('tf_efficientnetv2_b2' , 260, False, ""),
            ('tf_efficientnetv2_b3' , 300, False, ""),
        ]:
            if args.only_test and args.only_test not in name:
                continue

            print(f"Creating onnx runtime session: {name}")
            sess = ort.InferenceSession("onnx/%s.onnx" % name, sess_options=sess_options, providers=providers)
            args.model = name
            args.input_size = resolution
            args.usi_eval = usi_eval
            args.input_name = "input"
            args.output_name = "output"

            if args.validation:
                dataset_val = build_dataset(args)
                sampler_val = torch.utils.data.SequentialSampler(dataset_val)
                data_loader_val = torch.utils.data.DataLoader(
                    dataset_val,
                    sampler=sampler_val,
                    batch_size=args.batch_size,
                    num_workers=args.num_workers,
                    drop_last=False
                )
                args.len_dataset_val = len(dataset_val)
                evaluate(data_loader_val, sess, args)
            else:
                benchmarking_onnx(sess, load_image(args), args)

