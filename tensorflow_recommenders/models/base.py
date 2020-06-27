# Copyright 2020 The TensorFlow Recommenders Authors.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

# lint-as: python3
"""Base model."""

import tensorflow as tf


class Model(tf.keras.Model):
  """Base model for TFRS models.

  Many recommender models are relatively complex, and do not neatly fit into
  supervised or unsupervised paradigms. This base class makes it easy to
  define custom traininig and test losses for such complex models.

  This is done by asking the user to implement the following methods:
  - `__init__` to set up your model. Variable, task, loss, and metric
    initialization should go here.
  - `train_loss` to define the training loss. The method takes as input the
    raw features passed into the model, and returns a loss tensor for training.
    As part of doing so, it should also update the model's metrics.
  - [Optional] `test_loss` to define the test loss. If not supplied, the
    `train_loss` method will be used. Overriding this method will allow
    models to behave differently in training and evaluation. For example,
    it may be useful to compute a wider set of metrics in evaluation if these
    metrics are too expensive to compute during training.
  - [Optional] `call` to define how the model computes its predictions. This
    is not always necessary: for example, two-tower retrieval models have two
    well-defined submodels whose `call` methods are normally used directly.

  When building more complex models that require further flexbility (such
  as the ability to use different optimizers for different variables, or
  manipulating the gradients), please override the `train_step` and
  `test_step` methods directly. Keras has an excellent tutorial on how to
  do this [here](https://keras.io/guides/customizing_what_happens_in_fit/).
  """

  def train_loss(self, inputs, training: bool = True) -> tf.Tensor:
    """Defines the training loss.

    Args:
      inputs: A data structure of tensors: raw inputs to the model. These will
        usually contain labels and weights as well as features.
      training: Whether the model is in training mode.

    Returns:
      Loss tensor.
    """

    raise NotImplementedError(
        "Implementers must implement the `train_loss` method.")

  def test_loss(self, inputs) -> tf.Tensor:
    """Defines the test loss.

    Args:
      inputs: A data structure of tensors: raw inputs to the model. These will
        usually contain labels and weights as well as features.

    Returns:
      Loss tensor.
    """

    return self.train_loss(inputs)

  def train_step(self, inputs):
    """Custom train step using the `train_loss` method."""

    if isinstance(inputs, tuple) and len(inputs) == 1:
      # Keras has added a (features, labels) tuple; let's unpack it.
      inputs = inputs[0]

    with tf.GradientTape() as tape:
      loss = self.train_loss(inputs)

    gradients = tape.gradient(loss, self.trainable_variables)
    self.optimizer.apply_gradients(zip(gradients, self.trainable_variables))

    metrics = {metric.name: metric.result() for metric in self.metrics}
    metrics["loss"] = loss

    return metrics

  def test_step(self, inputs):
    """Custom test step using the `test_loss` method."""

    if isinstance(inputs, tuple) and len(inputs) == 1:
      # Keras has added a (features, labels) tuple; let's unpack it.
      inputs = inputs[0]

    loss = self.test_loss(inputs)

    metrics = {metric.name: metric.result() for metric in self.metrics}
    metrics["loss"] = loss

    return metrics