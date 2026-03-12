% 设定需要生成的行数 
% 原文件共有 893 行，对应最大时间为 26760 秒 (892 * 30)
num_rows = 893;

% 1. 生成 epoch_start_sec (从 0 开始，步长为 30)
epoch_start_sec = (0:30:(num_rows-1)*30)';

% 2. 模拟 mean_hr (心率数据)
% 均值约60.6，标准差约5.9的随机正态分布数据
mean_hr = 60.6 + 5.9 * randn(num_rows, 1);
% 对生成的心率进行上下限位处理，贴近原文件的波动范围 [50, 85]
mean_hr(mean_hr < 50) = 50 + rand(sum(mean_hr < 50), 1) * 5; 
mean_hr(mean_hr > 85) = 85 - rand(sum(mean_hr > 85), 1) * 5;

% 3. 计算 elapsed_hours (经过的小时数 = 秒数 / 3600)
elapsed_hours = epoch_start_sec / 3600;

% 4. 计算 progress (实验进度，归一化到 0 到 1)
progress = epoch_start_sec / max(epoch_start_sec);

% 5. 模拟 pred_stage_code (睡眠/预测阶段代码，1 到 5 的随机整数)
pred_stage_code = randi([1, 5], num_rows, 1);
pred_stage_code = double(pred_stage_code); % 转为浮点型以支持 NaN

% 模拟原始数据的特征：前9行没有生成预测代码，设为 NaN
pred_stage_code(1:9) = NaN;

% ==========================================
% 将数据合并
% ==========================================
T = table(epoch_start_sec, mean_hr, elapsed_hours, progress, pred_stage_code);

% ==========================================
% 自动命名逻辑：检查文件是否存在并递增序号
% ==========================================
base_filename = 'simulated_data_with_pred';
extension = '.csv';

% 首次尝试没有后缀数字的名字
filename = [base_filename, extension];
counter = 2;

% 如果文件已存在，则不断尝试 _2, _3, _4...
while isfile(filename)
    filename = sprintf('%s_%d%s', base_filename, counter, extension);
    counter = counter + 1;
end

% ==========================================
% 写入 CSV 文件
% ==========================================
writetable(T, filename);

disp(['模拟数据生成完毕！已保存至当前目录：', filename]);