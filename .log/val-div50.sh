python main.py --model efficientformerv2_s0 --weights weights/eformer_s0_450.pth --data-path imagenet-div50
python main.py --model efficientformerv2_s1 --weights weights/eformer_s1_450.pth --data-path imagenet-div50
python main.py --model efficientformerv2_s2 --weights weights/eformer_s2_450.pth --data-path imagenet-div50
python main.py --model SwiftFormer_XS --weights weights/SwiftFormer_XS_ckpt.pth --data-path imagenet-div50
python main.py --model SwiftFormer_S --weights weights/SwiftFormer_S_ckpt.pth --data-path imagenet-div50
python main.py --model SwiftFormer_L1 --weights weights/SwiftFormer_L1_ckpt.pth --data-path imagenet-div50
python main.py --model EMO_1M --weights weights/EMO_1M.pth --data-path imagenet-div50
python main.py --model EMO_2M --weights weights/EMO_2M.pth --data-path imagenet-div50
python main.py --model EMO_5M --weights weights/EMO_5M.pth --data-path imagenet-div50
python main.py --model EMO_6M --weights weights/EMO_6M.pth --data-path imagenet-div50
python main.py --model edgenext_xx_small --weights weights/edgenext_xx_small.pth --data-path imagenet-div50
python main.py --model edgenext_x_small --weights weights/edgenext_x_small.pth --data-path imagenet-div50
python main.py --model edgenext_small --weights weights/edgenext_small_usi.pth --data-path imagenet-div50
python main.py --model mobilevitv2_050 --weights weights/mobilevitv2-0.5.pt --data-path imagenet-div50
python main.py --model mobilevitv2_075 --weights weights/mobilevitv2-0.75.pt --data-path imagenet-div50
python main.py --model mobilevitv2_100 --weights weights/mobilevitv2-1.0.pt --data-path imagenet-div50
python main.py --model mobilevitv2_125 --weights weights/mobilevitv2-1.25.pt --data-path imagenet-div50
python main.py --model mobilevitv2_150 --weights weights/mobilevitv2-1.5.pt --data-path imagenet-div50
python main.py --model mobilevitv2_175 --weights weights/mobilevitv2-1.75.pt --data-path imagenet-div50
python main.py --model mobilevitv2_200 --weights weights/mobilevitv2-2.0.pt --data-path imagenet-div50
python main.py --model mobilevit_xx_small --weights weights/mobilevit_xxs.pt --data-path imagenet-div50
python main.py --model mobilevit_x_small --weights weights/mobilevit_xs.pt --data-path imagenet-div50
python main.py --model mobilevit_small --weights weights/mobilevit_s.pt --data-path imagenet-div50
python main.py --model LeViT_128S --weights weights/LeViT-128S-96703c44.pth --data-path imagenet-div50
python main.py --model LeViT_128 --weights weights/LeViT-128-b88c2750.pth --data-path imagenet-div50
python main.py --model LeViT_192 --weights weights/LeViT-192-92712e41.pth --data-path imagenet-div50
python main.py --model LeViT_256 --weights weights/LeViT-256-13b5763e.pth --data-path imagenet-div50

python main.py --model resnet50 --extern --data-path imagenet-div50
python main.py --model mobilenetv3_large_100 --extern --data-path imagenet-div50
python main.py --model tf_efficientnetv2_b0 --extern --data-path imagenet-div50
python main.py --model tf_efficientnetv2_b1 --extern --data-path imagenet-div50
python main.py --model tf_efficientnetv2_b2 --extern --data-path imagenet-div50
python main.py --model tf_efficientnetv2_b3 --extern --data-path imagenet-div50