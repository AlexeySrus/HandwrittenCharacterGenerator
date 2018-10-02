from cvae import create_cvae
from train_cvae import classes, read_sample, one_hot_vector, get_actual_area
import argparse
from keras.models import load_model
import numpy as np
import cv2


def argument_parser():
    arg_pars = argparse.ArgumentParser()
    arg_pars.add_argument('text', nargs='+',
                          help='Text for translate.')
    arg_pars.add_argument('--base-image', required=True,
                          help='Base style image path.')
    arg_pars.add_argument('--base-label', required=True,
                          help='Base label.',
                          choices=classes)
    arg_pars.add_argument('--model-path', required=True,
                          help='Model path.')
    arg_pars.add_argument('--batch-size', default=32, type=int,
                          help='Size of batch of images.')
    arg_pars.add_argument('--image-width', required=False,
                          type=int,
                          default=28)
    arg_pars.add_argument('--latentdim', required=False,
                          type=int,
                          default=2)
    return arg_pars.parse_args()


def gen_batch(elem, batch_size):
    return np.array([elem]*batch_size)


def get_latent_parameters(models, base_img_path, base_label, shape, batch_size):
    img, label = read_sample({
        'image_path': base_img_path,
        'label': base_label
    }, shape)

    return models['encoder'].predict(
        [
            np.reshape(
                gen_batch(img, batch_size), (batch_size, shape[0], shape[1], 1)
            ),
            gen_batch(label, batch_size)
        ]
    )[0]


def generate_image_by_character(models, label, batch_size, latent_parameters):
    return np.array(
        models['decoder'].predict(
            [
                gen_batch(latent_parameters, batch_size),
                gen_batch(one_hot_vector(label), batch_size)
            ]
        )[0] * 255,
        dtype=np.uint8
    )


if __name__ == '__main__':
    args = argument_parser()

    models, loss = create_cvae(
        batch_size=args.batch_size,
        latent_dim=args.latentdim,
        input_shape=(args.image_width, args.image_width),
        num_classes=len(classes),
        dropout_rate=0.0
    )

    models['cvae'].load_weights(args.model_path)

    latent_parameters = get_latent_parameters(
        models,
        args.base_image,
        args.base_label,
        (args.image_width, args.image_width),
        args.batch_size
    )

    print(latent_parameters)

    gen_img = generate_image_by_character(
        models,
        'W',
        args.batch_size,
        latent_parameters
    )

    print(models['cvae'].summary())

    window_name = 'Generated character'
    cv2.namedWindow(window_name, cv2.WINDOW_NORMAL)
    cv2.imshow(window_name, gen_img)
    cv2.waitKey()
