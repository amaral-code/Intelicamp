#!/usr/bin/env bash
kill $(lsof -ti:${PORT:-5001} 2>/dev/null) 2>/dev/null
echo "Servidor finalizado (porta ${PORT:-5001})"
