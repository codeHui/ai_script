@[TOC](这里写自定义目录标题)
本文主要是个人学习记录，请见谅不够详细和错字

# 硬件
1张Nvidia A100 80G 
# 部署模型
Lamma3.1 70b 4bit
4bit是指quantization，4bit是最小的（代表精度最低（模型大小最小），但性能最好，ollama只支持4bit）。我在ollama官网没看到是用的那个版本的4bit，llama官网也没看见不同quantization版本，所以我不确定Llama官方是否提供了不同quantization版本（知道的麻烦告知下）
# 硬件性能监控工具
## GPU监控工具
* 开源可视化工具nvitop
安装命令：pip install nvitop
运行命令：nvitop
![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/e253ef46b8f64e05a05fd037181c93ef.png)* Nvidia自带监控
watch -n 1 nvidia-smi
## CPU和系统内存监控工具
Linux的top命令（top后再按1，可以查看多核cpu每个核心的占用）

# 部署框架
https://github.com/ollama/ollama
## 命令

```
ollama pull llama3.1:70b
```

```
ollama run llama3.1:70b
```
## 测试脚本与结果
本次测试的最重要的结果是平均每个线程的每秒token生成数（生成的总token数 / 响应总时间），因为chatgpt是流式生成token（感兴趣的可以看[ChatGPT流式显示单词的技术实现](https://blog.csdn.net/qq_26843937/article/details/140819730)  ）的, 所以 tokens/second是直接影响用户体验的数据，衡量了llm的文字生成速度（一个token约等于一个文字）
### 输出定量token测试
#### prompt 
`tell a story in " + str(world_count) + " words:`
#### 脚本
https://github.com/codeHui/ai_script/blob/main/A100_80G_Llama3_70B/70b_output-stream.py

#### Test Result
| Number of Requests | Output Word Count | Average Tokens | Average Time (s) | Average Speed (tokens/s) |  
|--------------------|-------------|----------------|------------------|--------------------------|  
| 1                  | 25          | 28             | 1.22156          | 22.9214                  |  
| 1                  | 50          | 63             | 2.49925          | 25.2076                  |  
| 1                  | 100         | 119            | 4.68078          | 25.4231                  | 
| 1                  | 400         | 456            | 18.0439          | 25.2717                  |  
| 1                  | 800         | 821            | 32.9355          | 24.9275                  |   
| 2                  | 25          | 31             | 1.4789           | 20.9615                  |  
| 2                  | 50          | 60.5           | 2.84061          | 21.2983                  |  
| 2                  | 100         | 125            | 5.59961          | 22.323                   |  
| 2                  | 400         | 460.5          | 21.3357          | 21.5835                  |  
| 2                  | 800         | 877            | 42.0024          | 20.8798                  |  
| 4                  | 25          | 30.5           | 2.0107           | 15.1689                  |  
| 4                  | 50          | 66.5           | 4.21136          | 15.7906                  |  
| 4                  | 100         | 122.75         | 7.56207          | 16.232                   |  
| 4                  | 400         | 478.25         | 31.1035          | 15.3761                  |  
| 4                  | 800         | 1066.75        | 76.1915          | 14.0009                  |
### 输入定量token测试  
#### prompt 
`"give a title for below text in 10 words: "  + text` (text has 484 words)
#### 脚本
https://github.com/codeHui/ai_script/blob/main/A100_80G_Llama3_70B/70b_input-stream.py

#### Test Result

| Number of Requests | Output Word Count | Average Tokens | Average Time (s) | Average Speed (tokens/s) |  
|--------------------|-------------|----------------|------------------|--------------------------|  
| 1                  | 10          | 16             | 2.27796          | 7.02383                  |  
| 2                  | 10          | 19             | 2.63539          | 7.20955                  |  
| 4                  | 10          | 16.75          | 4.58825          | 3.65063                  |  

# 性能分析
## 系统内存和GPU内存占用变化分析
### 系统内存和GPU内存占用变化
![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/662e57caae954ab0ad4877e05965874b.png)
### 系统内存总结
如果部署40G的llm, 系统内存大于40G肯定行（小于不确定，没测过），系统会先将llm加载到系统内存中（比较慢，感觉1秒1G的速度），然后瞬间将40G的llm加载到GPU的内存。
之后并发请求测试也基本完全不会用到系统内存。
if the system memory is very big (220G, much bigger than the Llama3.1 70b(40G))
when execute ollama pull, the system memory will cache the llm file(40G)
when execute ollama run, the system memory will cache the llm file(40G) if not cached yet, once done, the llm file will be copied to GPU memory(VRAM) immediately
once the llm is running, there is no need for system memory to cache LLM

### GPU内存总结

 - 在并发测试中，GPU内存一直保持42G,并无增加，所以GPU内存大于LLM应该就行 同时我测了如果用

- 如果有两个A100 80G的话，ollama 也只会使用一个GPU(这里不多讨论多GPU的方案，也有很多细节)

## 系统CPU占用分析
我测试了，不管单个还是并发访问下，也只有一个CPU core接近满载80~100%运行（不确定为什么只会利用一个core的CPU,以及CPU在做什么计算工作？有知道的话麻烦评论告知我，谢谢）
由于只占用一个core，所以cpu肯定不是瓶颈

## GPU分析
- 问llm问题时，GPU基本满载，可以确定GPU决定了响应速度
- Llama最多会并发处理4个请求，超过的会先放到队列里，所以该设计能防止out of memory（把脚本改成8个并发，从响应时间可以看出超过4个的会放到队列里）
## 其他分析总结
 1. 由上面两个测试可以看出，虽然input和output都占用总token，但output的生成更慢 （所以可以解释到GPT-4o 的收费，也是output tokens比input tokens 贵）
# 其他考虑因素
## Context window
Llama3.1的context window是128k, 但我测试了“让llm生成3000字的故事”，实际只会返回1000多字的答案，所以某个地方应该有设置限制了响应的token数（我没深入查，如果有知道是哪里限制的（比如chat API的哪个字段），请告知下）。
所以我上面只测试了1000以下的token数（一般用户场景足够），但如果真的是用满了128k的context window，是否系统内存和gpu内存会有比较明显的提升，我也不敢确定（因为没测过，有测过的也可以share下）
![在这里插入图片描述](https://i-blog.csdnimg.cn/direct/f1ae9c5ac19041959ec186e3a09bbfd0.png)

