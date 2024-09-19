import gradio as gr


class SpeechApp:
    def __init__(self, model) -> None:
        self.ts = model

    def gradio(self):
        try:
            demo = gr.Interface(
                fn=self.ts.tts_speak_with_options,
                inputs=[
                    gr.Text(label="Text"),
                    gr.Textbox(label="Output Path", value="data/audio/output.wav"),
                ],
                outputs=[
                    gr.Audio(label="Audio"),
                ],
            )
            demo.launch()
        except Exception as e:
            print(f"Error in launching gradio demo: {e}")


if __name__ == "__main__":
    from text_to_speech import TTSModel

    app = SpeechApp(TTSModel())
    app.gradio()
