import torch
import torch.onnx
import tensorrt as trt
import numpy as np
import pycuda.driver as cuda
import pycuda.autoinit
import os

class ModelConverter:
    def __init__(self, workspace_dir, target_model_path, input_shape=(1, 3, 224, 224)):
        self.workspace_dir = workspace_dir
        self.target_model_path = target_model_path
        self.onnx_file_path = os.path.join(workspace_dir, "model.onnx")
        self.tensorrt_engine_path = os.path.join(workspace_dir, "model.trt")
        self.input_shape = input_shape
        self.TRT_LOGGER = trt.Logger(trt.Logger.WARNING)

    def convert_to_onnx(self):
        # Load the PyTorch model from the specified path
        pytorch_model = torch.load(self.target_model_path)
        pytorch_model.eval()  # Set to evaluation mode

        # Dummy input for tracing (must match model input size)
        dummy_input = torch.randn(*self.input_shape)

        # Export the model to an ONNX file
        torch.onnx.export(
            pytorch_model,                # Model to export
            dummy_input,                  # Model input (dummy data)
            self.onnx_file_path,          # Output ONNX file path
            export_params=True,           # Store the trained parameter weights
            opset_version=11,             # ONNX version
            do_constant_folding=True,     # Simplify the model
            input_names=['input'],        # Input name(s)
            output_names=['output']       # Output name(s)
        )
        print("Model has been successfully converted to ONNX format.")

    def convert_to_tensorrt(self):
        # Builder, Network and Parser
        builder = trt.Builder(self.TRT_LOGGER)
        network = builder.create_network(1 << int(trt.NetworkDefinitionCreationFlag.EXPLICIT_BATCH))
        parser = trt.OnnxParser(network, self.TRT_LOGGER)

        # Parse the ONNX file
        with open(self.onnx_file_path, 'rb') as model:
            if not parser.parse(model.read()):
                for error in range(parser.num_errors):
                    print(parser.get_error(error))
                raise ValueError("Failed to parse the ONNX file.")

        # Build the TensorRT engine
        builder.max_batch_size = 1
        builder.max_workspace_size = 1 << 30  # 1GB workspace

        config = builder.create_builder_config()
        config.max_workspace_size = 1 << 30

        print("Building TensorRT engine. This may take a while...")
        engine = builder.build_engine(network, config)

        # Save the engine to file
        with open(self.tensorrt_engine_path, "wb") as f:
            f.write(engine.serialize())

        print("TensorRT engine has been successfully saved.")

    def run_inference(self, input_data=None):
        if input_data is None:
            input_data = np.random.random(self.input_shape).astype(np.float32)

        # Load TensorRT runtime and engine
        runtime = trt.Runtime(self.TRT_LOGGER)
        with open(self.tensorrt_engine_path, "rb") as f:
            engine = runtime.deserialize_cuda_engine(f.read())

        # Create context
        context = engine.create_execution_context()

        # Allocate device memory
        output_shape = (1, 1000)
        
        # Allocate input and output buffers
        output_host = np.empty(output_shape, dtype=np.float32)

        input_device = cuda.mem_alloc(input_data.nbytes)
        output_device = cuda.mem_alloc(output_host.nbytes)

        # Transfer input data to the GPU
        cuda.memcpy_htod(input_device, input_data)

        # Run inference
        context.execute_v2(bindings=[int(input_device), int(output_device)])

        # Transfer predictions back from GPU
        cuda.memcpy_dtoh(output_host, output_device)

        print("Inference completed successfully.")
        print("Output:", output_host)  # Display output predictions

# Example usage
if __name__ == "__main__":
    converter = ModelConverter(workspace_dir="./models", target_model_path="./models/resnet50.pth")
    converter.convert_to_onnx()
    converter.convert_to_tensorrt()
    converter.run_inference()