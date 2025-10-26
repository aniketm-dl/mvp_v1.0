#!/bin/bash
# Simple script to check training status

echo "🔍 Checking training status..."
echo ""

# Check progress
PROGRESS=$(ssh -i ~/darpan-training-new.pem ubuntu@3.108.237.6 "cd ~/mvp_v1.0 && ls -la artifacts/llm_adapters/ | wc -l")
PROGRESS=$((PROGRESS - 2))  # Subtract 2 for . and ..

echo "📊 Progress: $PROGRESS/18 personas completed"

if [ "$PROGRESS" -ge 18 ]; then
    echo "✅ Training is COMPLETE!"
    echo ""
    echo "📥 To download models:"
    echo "   aws s3 sync s3://darpan-training-aniketniranjanmishra/trained_adapters/ artifacts/llm_adapters/"
    echo ""
    echo "🎭 To start chatting:"
    echo "   python interact_cli.py"
else
    echo "⏳ Training still in progress..."
    echo "   Estimated time remaining: $(( (18 - PROGRESS) * 5 )) minutes"
fi

echo ""
echo "💡 To monitor in real-time:"
echo "   watch -n 30 './check_training_status.sh'"
