# # 多类支持向量机练习
# 练习目标:
# - 实现一个完全向量化的 SVM **损失函数**
# - 实现其**解析梯度**的完全向量化表达
# - 使用数值梯度**检查实现**
# - 使用验证集**调整学习率和正则化**强度
# - 使用**随机梯度下降（SGD）**优化损失函数
# - **可视化**最终学习到的权重

import random
import numpy as np
from cs231n.data_utils import load_CIFAR10
import matplotlib.pyplot as plt
import matplotlib

matplotlib.rcParams['font.family'] = 'SimHei'
matplotlib.rcParams['axes.unicode_minus'] = False

# # get_ipython注释掉是因为，其作用是允许用户访问一些特定于 Notebook 的功能，在python文件中无用会报错
# get_ipython().run_line_magic('matplotlib', 'inline')
plt.rcParams['figure.figsize'] = (10.0, 8.0) # 设置图形的默认大小
plt.rcParams['image.interpolation'] = 'nearest' # 设置图像插值方法为最近邻插值
plt.rcParams['image.cmap'] = 'gray' # 设置图像的颜色映射为灰度

# 一些额外的魔法，使 notebook 自动重新加载外部 Python 模块；
# 这两行代码通过 IPython 扩展加载了自动重新加载模块的功能，使得在 notebook 中修改外部 Python 模块后，无需手动重新加载，便于开发和调试。
# get_ipython().run_line_magic('load_ext', 'autoreload')
# get_ipython().run_line_magic('autoreload', '2')


# ## CIFAR-10 数据加载和预处理
# 加载原始的 CIFAR-10 数据(这一部分的检验与KNN中相同)
cifar10_dir = 'cs231n/datasets/cifar-10-batches-py'
X_train, y_train, X_test, y_test = load_CIFAR10(cifar10_dir)

print('输出1：训练数据训练标签形状以及测试数据测试标签形状')
# 作为一种合理性检查，我们打印训练数据和测试数据的大小
print('Training data shape: ', X_train.shape)
print('Training labels shape: ', y_train.shape)
print('Test data shape: ', X_test.shape)
print('Test labels shape: ', y_test.shape)

# 从 CIFAR-10 数据集中可视化不同类别的样本图像
classes = ['plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']
num_classes = len(classes)
# 定义每个类别要显示的样本数量，这里设为 7。
samples_per_class = 7
# 使用 enumerate 函数遍历 classes 列表，y 表示类别索引，cls 表示类别名称
for y, cls in enumerate(classes):
    # 找出训练标签中等于当前类别索引 y 的所有样本的索引，返回一个一维数组 idxs
    idxs = np.flatnonzero(y_train == y)
    # 随机不重复选择7个样本索引
    idxs = np.random.choice(idxs, samples_per_class, replace=False)
    # 遍历选中的样本索引 idxs，计算绘图的位置索引，结合i与y定位当前图像在子图中的位置
    for i, idx in enumerate(idxs):
        plt_idx = i * num_classes + y + 1
        plt.subplot(samples_per_class, num_classes, plt_idx)
        # 显示选定样本的图像，将图像数据转换为无符号整数格式，确保图像正确显示。
        plt.imshow(X_train[idx].astype('uint8'))
        plt.axis('off')
        # 隐藏图像的坐标轴，使图像清晰可见
        if i == 0:
            plt.title(cls)
plt.show()
print('输出2（图像）：可视化不同类别的样本图像')

# 将数据分为训练集、验证集和测试集。此外，我们还将
# 创建一个小的开发集作为训练数据的子集；
# 我们可以使用这个开发集，以使代码运行更快。
# 设置数据集的大小：
num_training = 49000
num_validation = 1000
num_test = 1000
num_dev = 500

# 创建验证集
# 我们的验证集将从原始训练集中选取 num_validation 个点。
mask = list(range(num_training, num_training + num_validation))
X_val = X_train[mask]
y_val = y_train[mask]

# 创建训练集
# 我们的训练集将是原始训练集中前 num_training 个点。
mask = list(range(num_training))
X_train = X_train[mask]
y_train = y_train[mask]

# 我们还将创建一个开发集，它是训练集的一个小子集。
mask = np.random.choice(num_training, num_dev, replace=False)
X_dev = X_train[mask]
y_dev = y_train[mask]

# 我们将使用原始测试集的前 num_test 个点作为我们的测试集。
mask = list(range(num_test))
X_test = X_test[mask]
y_test = y_test[mask]

# 打印数据形状
print('输出3：训练数据、标签形状；验证数据、标签形状；测试数据、标签形状')
print('Train data shape: ', X_train.shape)
print('Train labels shape: ', y_train.shape)
print('Validation data shape: ', X_val.shape)
print('Validation labels shape: ', y_val.shape)
print('Test data shape: ', X_test.shape)
print('Test labels shape: ', y_test.shape)

# 将 CIFAR-10 数据集分为训练集、验证集、测试集和开发集。这种划分使得在模型训练和调试时，
# 可以有效地使用不同的数据集来进行验证和开发，从而提高代码运行效率和模型性能

# 预处理：将图像数据重塑为行
# np.reshape 函数将每个数据集的图像数据重塑为二维数组（行数为样本数量，列数为图像的像素数量）
X_train = np.reshape(X_train, (X_train.shape[0], -1))
X_val = np.reshape(X_val, (X_val.shape[0], -1))
X_test = np.reshape(X_test, (X_test.shape[0], -1))
X_dev = np.reshape(X_dev, (X_dev.shape[0], -1))

# 作为合理性检查，打印出数据的形状
print('输出4：重塑后数据集形状')
print('Training data shape: ', X_train.shape)
print('Validation data shape: ', X_val.shape)
print('Test data shape: ', X_test.shape)
print('dev data shape: ', X_dev.shape)
# 通过检查数据形状，确保在重塑过程中没有丢失数据，并且每个数据集的样本数量和特征数量都合理。


# 预处理：减去均值图像
# 首先：基于训练数据计算图像均值
mean_image = np.mean(X_train, axis=0)
print('输出5：输出平均图像数组的前十个元素')
print(mean_image[:10]) # 打印均值的一部分元素
# 打印出均值数组的前十个元素，以便观察这些像素值，帮助理解数据的分布特征。
plt.figure(figsize=(4,4))
# 将一维均值数组重新塑形为三维数组（高、宽、通道），这里图像尺寸为 32x32，通道数为 3（RGB）
# 将数据类型转换为无符号 8 位整数，以便正确显示图像
plt.imshow(mean_image.reshape((32,32,3)).astype('uint8')) # 可视化均值图像
plt.show()
print('输出6（图像）：均值图像')

# 第二步：从训练和测试数据中减去均值图像
X_train -= mean_image
X_val -= mean_image
X_test -= mean_image
X_dev -= mean_image

# 第三步：添加偏置维度的全1（即偏置技巧），使得我们的支持向量机（SVM）只需要优化一个权重矩阵 W
# 使用 np.hstack 将每个数据集的样本矩阵与一个全1的列向量水平拼接。
X_train = np.hstack([X_train, np.ones((X_train.shape[0], 1))])
X_val = np.hstack([X_val, np.ones((X_val.shape[0], 1))])
X_test = np.hstack([X_test, np.ones((X_test.shape[0], 1))])
X_dev = np.hstack([X_dev, np.ones((X_dev.shape[0], 1))])
# 打印各个数据集的形状，以便检查维度是否符合预期
print('输出7：预处理添加偏执维度后数据集形状')
print(X_train.shape, X_val.shape, X_test.shape, X_dev.shape)

# ## SVM 分类器
# 
# 此部分的代码将全部编写在linear_svm.py 文件中
# 正如看到的，我们已经预填充了 compute_loss_naive 函数，该函数使用 for 循环来计算多类 SVM 损失函数。

# 评估我们提供的损失的实现：
# 导入必要的模块
from cs231n.classifiers.linear_svm import svm_loss_naive
import time

# 生成一个随机的 SVM 权重矩阵，值较小
# 使用 np.random.randn(3073, 10) 生成一个形状为 (3073, 10) 的随机矩阵
# 其中每个元素遵循标准正态分布。
W = np.random.randn(3073, 10) * 0.0001 
# 乘以 0.0001 使得权重矩阵中的值较小，这样可以避免在训练过程中出现过大的更新

# 计算损失和梯度
# 调用 svm_loss_naive 函数，传入随机生成的权重矩阵W、开发集 、开发集标签以及一个小的正则化参数（0.00001）
loss, grad = svm_loss_naive(W, X_dev, y_dev, 0.00001)
print('输出8：损失值')
print('loss: %f' % (loss, ))
# 打印计算得到的损失值，以便检查模型在当前权重下的表现


# 返回的`grad`目前全为零。请推导并实现SVM成本函数的梯度，并将其内联实现到`svm_loss_naive`函数中。发现将新代码与现有函数交错实现会很有帮助。
# 为了检查您是否正确实现了梯度，可以通过数值估计损失函数的梯度，并将数值估计与您计算的梯度进行比较以下相应的代码：
print('输出9：梯度检查（数值梯度VS解析梯度）')
# 一旦实现了梯度，请使用下面的代码重新计算它
# 并使用我们为您提供的函数进行梯度检查

# 计算在 W 处的损失及其梯度。
# 调用 svm_loss_naive 函数计算在权重 W下的损失和梯度，这里未使用正则化（正则化参数为0）
loss, grad = svm_loss_naive(W, X_dev, y_dev, 0.0)

# 沿着几个随机选择的维度数值计算梯度，并
# 将其与分析计算的梯度进行比较。数字应该在所有维度上几乎完全匹配。
# 从 cs231n.gradient_check 导入 grad_check_sparse 函数，用于执行梯度检查
from cs231n.gradient_check import grad_check_sparse
# 函数f接受权重w作为输入，并计算其对应的 SVM 损失（返回损失的第一个值）
f = lambda w: svm_loss_naive(w, X_dev, y_dev, 0.0)[0]
# 调用 grad_check_sparse，将W和计算得到的 grad 传入，数值计算梯度并与分析计算的梯度进行比较，确保它们几乎完全匹配
grad_numerical = grad_check_sparse(f, W, grad)

# 再次在启用正则化的情况下进行梯度检查
# 再次调用 svm_loss_naive 函数，但这次传入了一个正则化参数（1e2），计算带有正则化的损失和梯度。
loss, grad = svm_loss_naive(W, X_dev, y_dev, 1e2)
f = lambda w: svm_loss_naive(w, X_dev, y_dev, 1e2)[0]
grad_numerical = grad_check_sparse(f, W, grad)


# ### 相关问题1:
# 在梯度检查中，有时某个维度的结果可能不会完全匹配。这种不匹配可能由什么原因引起？这是否值得关注？
# 请给出一个简单的一维示例，其中梯度检查可能会失败？提示：SVM损失函数严格来说不是可微分的。
# 
# **答案：** *当损失函数在某些点不可微分时，可能会导致不匹配。例如，ReLU 函数$f(x) = max(0,x)$ 在 x=0 处不可微分.
# 数值梯度的公式是$\frac{df(x)}{dx} = \frac{f(x+h)-f(x-h)}{2*h}$. 使用这个公式，
# 数值梯度是 $f'(\frac{h}{2}) = \frac{3}{4}$, 而解析梯度是 $f'(\frac{h}{2}) = 1$.因此，在靠近 $x=0$ 的点处产生了较大的差异。*


# 接下来实现函数 svm_loss_vectorized；现在只计算损失；
# 我们稍后再实现梯度。
tic = time.time()  # 记录当前时间
loss_naive, grad_naive = svm_loss_naive(W, X_dev, y_dev, 0.00001)  
# 使用朴素方法计算损失和梯度
toc = time.time()  # 记录当前时间
print('输出10：计算损失耗时比较（朴素方法VS向量化）')
print('Naive loss: %e computed in %fs' % (loss_naive, toc - tic))

# 输出朴素方法计算的损失和耗时
from cs231n.classifiers.linear_svm import svm_loss_vectorized 
# 从模块导入向量化的 SVM 损失函数
tic = time.time()  # 记录当前时间
loss_vectorized, _ = svm_loss_vectorized(W, X_dev, y_dev, 0.00001)  
# 使用向量化方法计算损失
toc = time.time()  # 记录当前时间
print('Vectorized loss: %e computed in %fs' % (loss_vectorized, toc - tic))  
# 输出向量化方法计算的损失和耗时

# 损失应该匹配，但向量化实现应该快得多。
print('difference: %f' % (loss_naive - loss_vectorized))  
# 输出两种方法计算的损失差异

# 完成 svm_loss_vectorized 的实现，并以向量化的方式计算损失函数的梯度。
# 朴素实现和向量化实现的结果应该匹配，但向量化版本仍然应该快得多。
tic = time.time()  # 记录当前时间
_, grad_naive = svm_loss_naive(W, X_dev, y_dev, 0.00001) 
# 使用朴素方法计算损失和梯度
toc = time.time()  # 记录当前时间
print('输出11：两种方法计算损失和梯度的耗时差异和梯度差异（朴素方法VS向量化）')
print('Naive loss and gradient: computed in %fs' % (toc - tic))  
# 输出朴素方法计算损失和梯度所需时间

tic = time.time()  # 记录当前时间
_, grad_vectorized = svm_loss_vectorized(W, X_dev, y_dev, 0.00001)
# 使用向量化方法计算损失和梯度
toc = time.time()  # 记录当前时间
print('Vectorized loss and gradient: computed in %fs' % (toc - tic))
# 输出向量化方法计算损失和梯度所需时间

# 损失是一个单一数值，因此比较两个实现计算的值很容易。
# 而梯度是一个矩阵，因此我们使用 Frobenius 范数来比较它们。
difference = np.linalg.norm(grad_naive - grad_vectorized, ord='fro')  
# 计算梯度的 Frobenius 范数
print('difference: %f' % difference)  # 输出梯度差异


# ### 随机梯度下降（SGD）
# 
# 我们现在已经得到了损失、梯度的向量化和高效表达式，并且我们的梯度与数值梯度匹配。因此，我们可以准备使用随机梯度下降（SGD）来最小化损失。
# 在文件 linear_classifier.py 中，实现 SGD（随机梯度下降）在函数
# LinearClassifier.train() 中，然后使用以下代码运行它。
from cs231n.classifiers import LinearSVM  
# 从 cs231n.classifiers 导入 LinearSVM
svm = LinearSVM()  # 实例化一个线性支持向量机（SVM）对象
tic = time.time()  # 记录当前时间
# X_train 和 y_train 是训练数据和对应标签；
# learning_rate=1e-7 设置学习率，决定每次参数更新的步长。
# reg=5e4 是正则化强度，帮助防止过拟合。
# num_iters=1500 指定训练的迭代次数。
# verbose=True 表示在训练过程中输出详细信息
print('输出12：训练过程中损失值历史')
loss_hist = svm.train(X_train, y_train, learning_rate=1e-7, reg=5e4,
                      num_iters=1500, verbose=True)  # 训练模型并返回损失历史
toc = time.time()  # 记录当前时间
print('输出13：训练时间')
print('That took %fs' % (toc - tic))  # 输出训练所需时间

# 一种有用的调试策略是将损失值绘制为迭代次数的函数：
plt.plot(loss_hist)  # 绘制损失历史
plt.xlabel('Iteration number')  # 设置 x 轴标签为“迭代次数”
plt.ylabel('Loss value')  # 设置 y 轴标签为“损失值”
plt.show()  # 显示图形
print('输出14（图像）：损失值随迭代次数变化的曲线')

# 编写 LinearSVM.predict 函数，并评估训练集和验证集的性能
y_train_pred = svm.predict(X_train)  # 在训练集上进行预测
print('输出15：训练集和验证集预测结果（准确率）')
print('training accuracy: %f' % (np.mean(y_train == y_train_pred), ))  # 输出训练准确率
y_val_pred = svm.predict(X_val)  # 在验证集上进行预测
print('validation accuracy: %f' % (np.mean(y_val == y_val_pred), ))  # 输出验证准确率


# 使用验证集来调整超参数（正则化强度和学习率）。
# 你应该尝试不同范围的学习率和正则化强度；如果你小心谨慎的话，应该能够在验证集上获得大约 0.4 的分类准确率。

# 超参数：learning_rates 列表定义了要尝试的学习率；regularization_strengths 列表通过组合生成了正则化强度的范围
learning_rates = [1.4e-7, 1.5e-7, 1.6e-7]
regularization_strengths = [(1 + i * 0.1) * 1e4 for i in range(-3, 3)] + [(2 + 0.1 * i) * 1e4 for i in range(-3, 3)]

# results 是一个字典，将形式为
# (learning_rate, regularization_strength) 的元组映射到形式为
# (training_accuracy, validation_accuracy) 的元组。准确率只是正确分类的数据点的比例。
results = {}
best_val = -1   # 到目前为止我们见过的最高验证准确率。
best_svm = None # 实现最高验证率的 LinearSVM 对象。

#############################################################################
# TODO:                                                                       
# 编写代码，通过在验证集上调整超参数选择最佳超参数。对于每种超参数组合，
# 在训练集上训练一个线性 SVM，计算其在训练集和验证集上的准确率，并
# 将这些数字存储在结果字典中。此外，将最佳验证准确率存储在 best_val 中，
# 将实现此准确率的 LinearSVM 对象存储在 best_svm 中。                 
# 提示：在开发验证代码时，应为 num_iters 使用较小的值，以便 SVM 不会花费太多时间进行训练；
# 一旦你对验证代码的工作有信心，应该使用更大的 num_iters 值重新运行验证代码。       
#############################################################################
# 超参数调优过程，使用嵌套循环遍历所有的学习率和正则化强度组合
for rs in regularization_strengths:
    for lr in learning_rates:
        svm = LinearSVM()  # 创建线性SVM模型
        # 训练模型
        loss_hist = svm.train(X_train, y_train, lr, rs, num_iters=3000)  
        y_train_pred = svm.predict(X_train)  # 在训练集上进行预测
        train_accuracy = np.mean(y_train == y_train_pred)  # 计算训练集准确率
        y_val_pred = svm.predict(X_val)  # 在验证集上进行预测
        val_accuracy = np.mean(y_val == y_val_pred)  # 计算验证集准确率
        if val_accuracy > best_val:  # 如果当前验证准确率更高
            best_val = val_accuracy  # 更新最佳验证准确率
            best_svm = svm  # 更新最佳模型
        results[(lr, rs)] = train_accuracy, val_accuracy  # 存储结果

# 打印结果
print('输出16：调优过程中不同超参数组合下验证集准确率')
for lr, reg in sorted(results):
    train_accuracy, val_accuracy = results[(lr, reg)]
    print('lr %e reg %e train accuracy: %f val accuracy: %f' % (
                lr, reg, train_accuracy, val_accuracy))

print('输出17：最佳验证集准确率')
print('best validation accuracy achieved during cross-validation: %f' % best_val)  # 打印最佳验证准确率


# 可视化交叉验证结果
# x轴：学习率对数值 y轴：正则化强度 散点：颜色越深，准确率越高
import math
x_scatter = [math.log10(x[0]) for x in results]  # 计算学习率的对数
y_scatter = [math.log10(x[1]) for x in results]  # 计算正则化强度的对数

# 绘制训练准确率
marker_size = 100  # 设置散点标记的大小
colors = [results[x][0] for x in results]  # 提取训练准确率作为颜色
plt.subplot(2, 1, 1)  # 创建2行1列的子图，选择第一个子图
plt.scatter(x_scatter, y_scatter, marker_size, c=colors)  # 绘制散点图
plt.colorbar()  # 添加颜色条
plt.xlabel('log learning rate')  # x轴标签
plt.ylabel('log  regularization strength')  # y轴标签
plt.title('CIFAR-10 training accuracy')  # 子图标题

# 绘制验证准确率
colors = [results[x][1] for x in results]  # 提取验证准确率作为颜色
plt.subplot(2, 1, 2)  # 选择第二个子图
plt.scatter(x_scatter, y_scatter, marker_size, c=colors)  # 绘制散点图
plt.colorbar()  # 添加颜色条
plt.xlabel('log learning rate')  # x轴标签
plt.ylabel('log regularization strength')  # y轴标签
plt.title('CIFAR-10 validation accuracy')  # 子图标题
plt.show()  # 显示图形
print('输出18（图像）：可视化交叉验证结果（不同超参数组合下正确率）')
# 可视化方法在模型调优过程中非常有用，可以帮助发现最佳的超参数组合。

# 在测试集上评估最佳的支持向量机 (SVM)
y_test_pred = best_svm.predict(X_test)  # 使用最佳 SVM 对测试数据进行预测
test_accuracy = np.mean(y_test == y_test_pred)  # 计算测试集的准确率
# 输出测试集的准确率
print('输出19：测试集的准确率')
print('linear SVM on raw pixels final test set accuracy: %f' % test_accuracy)


# 可视化每个类别学习到的权重。
# 根据你选择的学习率和正则化强度，这些权重可能
# 看起来很好，也可能不太好看。
w = best_svm.W[:-1, :]  # 去掉偏置项
w = w.reshape(32, 32, 3, 10)  # 重塑权重以适应图像的形状
w_min, w_max = np.min(w), np.max(w)  # 获取权重的最小值和最大值
classes = ['plane', 'car', 'bird', 'cat', 'deer', 'dog', 'frog', 'horse', 'ship', 'truck']
for i in range(10):
  plt.subplot(2, 5, i + 1) # 创建一个2行5列的子图
  # 将权重重缩放到0到255之间，以便将其转换为图像格式（像素值）
  wimg = 255.0 * (w[:, :, :, i].squeeze() - w_min) / (w_max - w_min)
  # 显示归一化后的权重图像，并将数据类型转换为无符号整数，以适应图像显示要求。
  plt.imshow(wimg.astype('uint8'))
  plt.axis('off')  # 关闭坐标轴，使图像更清晰
  plt.title(classes[i])  # 设置图像标题为类别名称
plt.show()
print('输出20（图像）：可视化数据集中每个类别学习到的权重')
# ### 相关问题2:
# 描述你的可视化SVM权重是什么样子的，并简要解释为什么它们看起来是这样的。
# 
# **答案：** *可视化的 SVM 权重看起来像是对应物体的平均轮廓（外形），这些是模型应该响应的特征。
# 因为得分是样本与相应权重之间的内积，如果我们希望在正确标签上得到更高的得分，那么对应的权重应该与样本更加平行。*