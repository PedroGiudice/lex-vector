#!/usr/bin/env bash
#
# test-learning.sh - Testa sistema de learning do Prompt Enhancer
#

set -e

echo "🧪 Testing Prompt Enhancer Learning System"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo

# Test 1: Repetir termo técnico 5x para criar pattern customizado
echo "Test 1: Auto-learning custom pattern (5x repetition)..."
for i in {1..5}; do
  echo '{"userPrompt": "preciso integrar com a API do superTech para baixar dados"}' | node .claude/hooks/prompt-enhancer.js > /dev/null 2>&1 || true
done

if [ -f .claude/hooks/lib/user-vocabulary.json ]; then
  echo "  ✅ Vocabulary file created"
  term_count=$(node -e "const fs=require('fs'); const v=JSON.parse(fs.readFileSync('.claude/hooks/lib/user-vocabulary.json')); console.log(Object.keys(v.terms).length);")
  echo "  📚 Terms learned: $term_count"

  custom_patterns=$(node -e "const fs=require('fs'); const v=JSON.parse(fs.readFileSync('.claude/hooks/lib/user-vocabulary.json')); console.log(v.customPatterns.length);")
  echo "  🎯 Custom patterns created: $custom_patterns"
else
  echo "  ❌ Vocabulary file not created"
fi
echo

# Test 2: Confidence tracking
echo "Test 2: Pattern confidence tracking..."
if [ -f .claude/hooks/lib/pattern-confidence.json ]; then
  echo "  ✅ Confidence file created"

  pattern_count=$(node -e "const fs=require('fs'); const c=JSON.parse(fs.readFileSync('.claude/hooks/lib/pattern-confidence.json')); console.log(Object.keys(c.patterns).length);")
  echo "  📊 Patterns tracked: $pattern_count"

  if [ "$pattern_count" -gt 0 ]; then
    avg_conf=$(node -e "const fs=require('fs'); const c=JSON.parse(fs.readFileSync('.claude/hooks/lib/pattern-confidence.json')); const patterns=Object.values(c.patterns); const avg=patterns.reduce((sum,p)=>sum+p.confidenceScore,0)/patterns.length; console.log(Math.round(avg));")
    echo "  💯 Average confidence: $avg_conf%"
  fi
else
  echo "  ❌ Confidence file not created"
fi
echo

# Test 3: Visualizar dados aprendidos
echo "Test 3: Learning data inspection..."
echo
echo "📚 Most frequent terms:"
if [ -f .claude/hooks/lib/user-vocabulary.json ]; then
  node -e "const fs=require('fs'); const v=JSON.parse(fs.readFileSync('.claude/hooks/lib/user-vocabulary.json')); const sorted=Object.entries(v.terms).sort((a,b)=>b[1].count-a[1].count).slice(0,5); sorted.forEach(([term,data])=>console.log(\`  - \${term}: \${data.count}x\`));"
fi
echo

echo "📊 Pattern confidence scores:"
if [ -f .claude/hooks/lib/pattern-confidence.json ]; then
  node -e "const fs=require('fs'); const c=JSON.parse(fs.readFileSync('.claude/hooks/lib/pattern-confidence.json')); Object.entries(c.patterns).forEach(([id,data])=>console.log(\`  - \${id}: \${data.confidenceScore}% (\${data.successfulTranslations}/\${data.totalMatches})\`));"
fi
echo

echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "✅ Learning system test complete!"
