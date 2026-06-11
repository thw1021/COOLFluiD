#!/bin/bash
# ============================================================
# fix_exception_specs.sh
# COOLFluiD C++11 → C++17 迁移：移除所有 throw() 动态异常规范
#
# 使用方法：在 COOLFluiD 根目录执行
#   bash tools/fix_exception_specs.sh
# ============================================================

set -e
cd "$(git rev-parse --show-toplevel 2>/dev/null || echo .)"

echo "========================================"
echo "移除 C++ 动态异常规范（throw()）"
echo "目标：使源码兼容 C++17"
echo "========================================"

echo ""
echo "[1/6] logcpp ..."
sed -i 's/throw()//'                                              src/logcpp/Category.cpp
sed -i 's/throw(std::invalid_argument)//'                          src/logcpp/Priority.cpp
echo "  [OK] src/logcpp/"

echo ""
echo "[2/6] Common - Exception::what() noexcept ..."
sed -i 's/virtual const char\* what() const throw()/virtual const char* what() const noexcept/' src/Common/Exception.hh
sed -i 's/const char\* what() const throw()/const char* what() const noexcept/'               src/Common/Exception.cxx
echo "  [OK] src/Common/Exception.hh/.cxx (what() noexcept)"

echo ""
echo "[3/6] Common - 异常类构造函数 throw() ..."
sed -i 's/throw()//'                                              src/Common/FilesystemException.cxx
sed -i 's/throw()//'                                              src/Common/NoSuchValueException.cxx
sed -i 's/throw()//'                                              src/Common/ParserException.cxx
echo "  [OK] src/Common/ (FilesystemException, NoSuchValueException, ParserException)"

echo ""
echo "[4/6] Common - 头文件 throw() 声明 ..."
for f in \
  src/Common/BadValueException.hh \
  src/Common/FailedAssertionException.hh \
  src/Common/FailedCastException.hh \
  src/Common/FileFormatException.hh \
  src/Common/FloatingPointException.hh \
  src/Common/LibLoader.hh \
  src/Common/MPI/MPIException.hh \
  src/Common/NoSuchStorageException.hh \
  src/Common/NotImplementedException.hh \
  src/Common/OSystem.hh \
  src/Common/SetupException.hh \
  src/Common/StorageExistsException.hh \
  src/Common/URLException.hh \
  src/Config/BadMatchException.hh \
  src/Config/ConfigOptionException.hh \
  src/Config/DuplicateNameException.hh \
  src/Config/NoEnvVarException.hh \
  src/Config/OptionValidationException.hh \
  src/Environment/ModuleLoadFailedException.hh \
  src/Framework/BadFormatException.hh \
  src/Framework/CallWithNoEffectException.hh \
  src/Framework/CollaboratorException.hh \
  src/Framework/ConsistencyException.hh \
  src/Framework/NegativeVolumeException.hh \
  src/Framework/TrsNotFoundException.hh \
  src/MathTools/FindMinimum.hh \
  src/MathTools/OutOfBoundsException.hh
do
  sed -i 's/throw()//' "$f"
done
echo "  [OK] 27 个头文件 throw() 声明已移除"

echo ""
echo "[5/6] Framework - InterpolatorRegister ..."
sed -i '/throw (Common::NoSuchValueException)/d'                  src/Framework/InterpolatorRegister.hh
sed -i '/throw (Common::NoSuchValueException)/d'                  src/Framework/InterpolatorRegister.cxx
echo "  [OK] src/Framework/InterpolatorRegister"

echo ""
echo "[6/6] THOR2CFmesh ..."
sed -i '/throw (Framework::NegativeVolumeException)/d'            plugins/THOR2CFmesh/CheckNodeNumberingHexa.hh
sed -i '/throw (Framework::NegativeVolumeException)/d'            plugins/THOR2CFmesh/CheckNodeNumberingHexa.cxx
echo "  [OK] plugins/THOR2CFmesh/"

echo ""
echo "========================================"
echo "验证：检查是否还有残留的 throw() 异常规范 ..."
REMAINING=$(grep -rn "throw\s*(" --include="*.hh" --include="*.cxx" --include="*.cpp" src/ plugins/ 2>/dev/null | grep -v "//.*throw" | grep -v "BOOST_|_GLIBCXX_" || true)
if [ -z "$REMAINING" ]; then
  echo "  ✅ 所有 throw() 动态异常规范已移除"
else
  echo "  ⚠️  以下文件可能还有残留，请手动检查："
  echo "$REMAINING"
fi
echo "========================================"
