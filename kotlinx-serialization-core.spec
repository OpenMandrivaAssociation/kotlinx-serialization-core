Name:		kotlinx-serialization-core
Version:	1.13.0
Release:	1
Summary:	Kotlin serialization core for the JVM
Group:		Development/Java
License:	Apache-2.0
URL:		https://github.com/Kotlin/kotlinx.serialization
# kotlinx.serialization tag v1.13.0.
# JVM classes for the catalog coordinate kotlinx-serialization-core.
# Upstream publishes that artifactId as a pom that points at the -jvm jar.
Source0:	kotlinx-serialization-core-%{version}.tar.gz

BuildArch:	noarch
BuildRequires:	java-21-openjdk-devel
BuildRequires:	kotlin
# kotlin-stdlib.jar is the unversioned jar from kotlin-libs.
# mvn(kotlin-stdlib) installs only kotlin-stdlib-2.4.21.jar.
BuildRequires:	kotlin-libs
BuildRequires:	sysjar
BuildRequires:	javapackages-filesystem
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-stdlib)
BuildRequires:	mvn(org.jetbrains.kotlin:kotlin-time-instant)

%description
org.jetbrains.kotlinx:kotlinx-serialization-core %{version}.
JVM core serializers from tag v1.13.0, compiled with kotlinc 2.0.21.
InstantSerializer needs kotlin.time.Instant from kotlin-time-instant
2.4.21 because the installed stdlib 2.0.21 has no Instant type.
Two IgnorableReturnValue annotations are omitted. They only affect the
return-value checker. One reserved discard binding is evaluated as a
bare Class.forName call so the ClassValue probe still runs.

%prep
%autosetup -n kotlinx-serialization-core-%{version}
find . -type f \( -name '*.jar' -o -name '*.class' -o -name '*.so' -o -name '*.node' -o -name '*.wasm' \) -print > binaries.list
if [ -s binaries.list ]; then
	cat binaries.list
	exit 1
fi
python3 - << 'PY'
from pathlib import Path
files = list(Path("src").rglob("*.kt"))
ign = 0
disc = 0
for p in files:
    text = p.read_text()
    ign += text.count("@IgnorableReturnValue\n")
    disc += text.count("val _ = ")
    text = text.replace("@IgnorableReturnValue\n", "")
    text = text.replace("val _ = ", "")
    p.write_text(text)
if len(files) != 54 or ign != 2 or disc != 1:
    raise SystemExit("patch counts files=" + str(len(files)) + " ign=" + str(ign) + " disc=" + str(disc))
for p in files:
    text = p.read_text()
    if "@IgnorableReturnValue" in text or "val _ = " in text:
        raise SystemExit("patch leftover " + str(p))
PY

%build
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
STDLIB=%{_javadir}/kotlin-stdlib.jar
INSTANT=%{_javadir}/kotlin-time-instant.jar
test -s "$STDLIB"
test -s "$INSTANT"
mkdir -p classes
find src -name '*.kt' | sort > sources.list
find src/common -name '*.kt' | sort > common.list
test "$(wc -l < sources.list)" -eq 54
test "$(wc -l < common.list)" -eq 50
common=$(paste -sd, common.list)
kotlinc -J-Xmx2g -jvm-target 1.8 -language-version 2.0 -no-stdlib \
	-Xmulti-platform -Xexpect-actual-classes \
	-Xcommon-sources="$common" \
	-opt-in=kotlinx.serialization.InternalSerializationApi \
	-opt-in=kotlinx.serialization.ExperimentalSerializationApi \
	-opt-in=kotlinx.serialization.SealedSerializationApi \
	-opt-in=kotlin.ExperimentalSubclassOptIn \
	-opt-in=kotlin.time.ExperimentalTime \
	-opt-in=kotlin.uuid.ExperimentalUuidApi \
	-opt-in=kotlin.ExperimentalMultiplatform \
	-cp "$STDLIB:$INSTANT" -d classes @sources.list
test "$(find classes -name '*.class' | wc -l)" -eq 229
test -s classes/kotlinx/serialization/SerializersKt.class
test -s classes/kotlinx/serialization/internal/InstantSerializer.class
test -s classes/kotlinx/serialization/internal/UuidSerializer.class
printf '%s\n' \
	'Manifest-Version: 1.0' \
	'Automatic-Module-Name: kotlinx.serialization.core' \
	'Implementation-Version: %{version}' \
	'Require-Kotlin-Version: 1.8' > manifest.mf
jar cfm kotlinx-serialization-core.jar manifest.mf -C classes .
jar i kotlinx-serialization-core.jar
desc=$(jar --describe-module --file kotlinx-serialization-core.jar)
printf '%s\n' "$desc"
if printf '%s\n' "$desc" | grep -F -q 'Unable'; then
	exit 1
fi
printf '%s\n' "$desc" | grep -F -qx 'kotlinx.serialization.core automatic'
cat > kotlinx-serialization-core.pom << END
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>
  <groupId>org.jetbrains.kotlinx</groupId>
  <artifactId>kotlinx-serialization-core</artifactId>
  <version>%{version}</version>
  <name>kotlinx-serialization-core</name>
  <description>Kotlin serialization core for the JVM</description>
  <url>https://github.com/Kotlin/kotlinx.serialization</url>
  <licenses>
    <license>
      <name>Apache-2.0</name>
      <url>https://www.apache.org/licenses/LICENSE-2.0.txt</url>
    </license>
  </licenses>
  <dependencies>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-stdlib</artifactId>
      <version>2.0.21</version>
    </dependency>
    <dependency>
      <groupId>org.jetbrains.kotlin</groupId>
      <artifactId>kotlin-time-instant</artifactId>
      <version>2.4.21</version>
    </dependency>
  </dependencies>
</project>
END

%install
set -eo pipefail
sysjar install --buildroot %{buildroot} \
	--artifact kotlinx-serialization-core.pom:kotlinx-serialization-core.jar \
	--file-name kotlinx-serialization-core \
	--filelist .mfiles
idx="%{buildroot}/usr/share/sysjar/index/org.jetbrains.kotlinx/kotlinx-serialization-core.sysjar"
test -s "$idx"
grep -F -q '"version": "%{version}"' "$idx"
grep -F -q '"artifactId": "kotlinx-serialization-core"' "$idx"
test -s %{buildroot}%{_javadir}/kotlinx-serialization-core.jar

%check
set -eo pipefail
export JAVA_HOME=%{_jvmdir}/java-21-openjdk
export PATH="$JAVA_HOME/bin:/usr/bin:/bin"
JAR=%{buildroot}%{_javadir}/kotlinx-serialization-core.jar
STDLIB=%{_javadir}/kotlin-stdlib.jar
INSTANT=%{_javadir}/kotlin-time-instant.jar
test -s "$JAR"
mkdir -p check
cat > check/Probe.kt << 'EOF'
import kotlinx.serialization.builtins.serializer

fun main() {
    val ser = String.serializer()
    val name = ser.descriptor.serialName
    if (name != "kotlin.String") error("name")
    println("kotlinx_serialization_core_ok " + name)
}
EOF
kotlinc -J-Xmx1g -jvm-target 1.8 -language-version 2.0 \
	-cp "$JAR:$STDLIB:$INSTANT" -d check/out check/Probe.kt
java -cp "check/out:$JAR:$STDLIB:$INSTANT" ProbeKt > check/out.txt
cat check/out.txt
grep -F -qx 'kotlinx_serialization_core_ok kotlin.String' check/out.txt

%files -f .mfiles
%license LICENSE.txt
